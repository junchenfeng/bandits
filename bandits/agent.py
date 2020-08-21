import numpy as np
import pymc3 as pm


class Agent(object):
    """
    An Agent is able to take one of a set of actions at each time step. The
    action is chosen using a strategy based on the history of prior actions
    and outcome observations.
    """

    def __init__(self, bandit, policy, prior=0, gamma=None):
        self.policy = policy
        self.k = bandit.k
        self.prior = prior
        self.gamma = gamma
        self._value_estimates = prior * np.ones(self.k)
        self.action_attempts = np.zeros(self.k)
        self.t = 0
        self.last_action = None

    def __str__(self):
        return "f/{}".format(str(self.policy))

    def reset(self):
        """
        Resets the agent's memory to an initial state.
        """
        self._value_estimates[:] = self.prior
        self.action_attempts[:] = 0
        self.last_action = None
        self.t = 0

    def choose(self):
        action = self.policy.choose(self)
        self.last_action = action
        return action

    def observe(self, reward):
        self.action_attempts[self.last_action] += 1

        if self.gamma is None:
            g = 1 / self.action_attempts[self.last_action]
        else:
            g = self.gamma
        q = self._value_estimates[self.last_action]

        self._value_estimates[self.last_action] += g * (reward - q)
        self.t += 1

    @property
    def value_estimates(self):
        return self._value_estimates


class GradientAgent(Agent):
    """
    The Gradient Agent learns the relative difference between actions instead of
    determining estimates of reward values. It effectively learns a preference
    for one action over another.
    """

    def __init__(self, bandit, policy, prior=0, alpha=0.1, baseline=True):
        super(GradientAgent, self).__init__(bandit, policy, prior)
        self.alpha = alpha
        self.baseline = baseline
        self.average_reward = 0

    def __str__(self):
        return "g/\u03B1={}, bl={}".format(self.alpha, self.baseline)

    def observe(self, reward):
        self.action_attempts[self.last_action] += 1

        if self.baseline:
            diff = reward - self.average_reward
            self.average_reward += 1 / np.sum(self.action_attempts) * diff

        pi = np.exp(self.value_estimates) / np.sum(np.exp(self.value_estimates))

        ht = self.value_estimates[self.last_action]
        ht += self.alpha * (reward - self.average_reward) * (1 - pi[self.last_action])
        self._value_estimates -= self.alpha * (reward - self.average_reward) * pi
        self._value_estimates[self.last_action] = ht
        self.t += 1

    def reset(self):
        super(GradientAgent, self).reset()
        self.average_reward = 0


class BetaAgent(Agent):
    """
    The Beta Agent is a Bayesian approach to a bandit problem with a Bernoulli
     or Binomial likelihood, as these distributions have a Beta distribution as
     a conjugate prior.
    """

    def __init__(self, bandit, policy, ts=True):
        super(BetaAgent, self).__init__(bandit, policy)
        self.n = bandit.n
        self.ts = ts
        self.model = pm.Model()
        with self.model:
            self._prior = pm.Beta(
                "prior",
                alpha=np.ones(self.k),
                beta=np.ones(self.k),
                shape=(1, self.k),
                transform=None,
            )
        self._value_estimates = np.zeros(self.k)

    def __str__(self):
        if self.ts:
            return "b/TS"
        else:
            return "b/{}".format(str(self.policy))

    def reset(self):
        super(BetaAgent, self).reset()
        self._prior.distribution.alpha = np.ones(self.k)
        self._prior.distribution.beta = np.ones(self.k)

    def observe(self, reward):
        self.action_attempts[self.last_action] += 1

        self.alpha[self.last_action] += reward
        self.beta[self.last_action] += self.n - reward

        if self.ts:
            self._value_estimates = self._prior.random()
        else:
            self._value_estimates = self.alpha / (self.alpha + self.beta)
        self.t += 1

    @property
    def alpha(self):
        return self._prior.distribution.alpha

    @property
    def beta(self):
        return self._prior.distribution.beta


class FrequentistAgent(Agent):
    def __str__(self):
        return "Freq-A"

    def __init__(self, bandit, policy):
        super(FrequentistAgent, self).__init__(bandit, policy)
        self.n = -1
        self.num_arm = max(self.value_estimates.shape)
        self._last_choice = 0
        self._optimal_choice = None

    def rand_choice(self):

        self.n += 1
        if self.n > 0:
            # absolute even distribution
            self._last_choice = (
                self._last_choice + 1 if self._last_choice != self.num_arm else 0
            )
        return self._last_choice

    def optimize(self):
        self._optimal_choice = np.argmax(self.value_estimates)

    def optimal_choice(self):
        return self._optimal_choice

    def reset(self):
        self.n = -1
        self._last_choice = 0
        self._optimal_choice = None
