import numpy as np


class Policy(object):
    """
    A policy prescribes an action to be taken based on the memory of an agent.
    """

    def __str__(self):
        return "generic policy"

    def choose(self, agent):
        return 0


class EpsilonGreedyPolicy(Policy):
    """
    The Epsilon-Greedy policy will choose a random action with probability
    epsilon and take the best apparent approach with probability 1-epsilon. If
    multiple actions are tied for best choice, then a random action from that
    subset is selected.
    """

    def __init__(self, epsilon):
        self.epsilon = epsilon

    def __str__(self):
        return "\u03B5-greedy (\u03B5={})".format(self.epsilon)

    def choose(self, agent):
        if np.random.random() < self.epsilon:
            return np.random.choice(len(agent.value_estimates))
        else:
            action = np.argmax(agent.value_estimates)
            if len(agent.value_estimates.shape) > 1:
                dim = max(agent.value_estimates.shape)
                value_estimates = agent.value_estimates.reshape(dim,)
            else:
                value_estimates = agent.value_estimates
            check = np.where(value_estimates == value_estimates[action])[0]
            if len(check) == 1:
                return action
            else:
                return np.random.choice(check)


class GreedyPolicy(EpsilonGreedyPolicy):
    """
    The Greedy policy only takes the best apparent action, with ties broken by
    random selection. This can be seen as a special case of EpsilonGreedy where
    epsilon = 0 i.e. always exploit.
    """

    def __init__(self):
        super(GreedyPolicy, self).__init__(0)

    def __str__(self):
        return "greedy"


class RandomPolicy(EpsilonGreedyPolicy):
    """
    The Random policy randomly selects from all available actions with no
    consideration to which is apparently best. This can be seen as a special
    case of EpsilonGreedy where epsilon = 1 i.e. always explore.
    """

    def __init__(self):
        super(RandomPolicy, self).__init__(1)

    def __str__(self):
        return "random"


class UCBPolicy(Policy):
    """
    The Upper Confidence Bound algorithm (UCB1). It applies an exploration
    factor to the expected value of each arm which can influence a greedy
    selection strategy to more intelligently explore less confident options.
    """

    def __init__(self, c):
        self.c = c

    def __str__(self):
        return "UCB (c={})".format(self.c)

    def choose(self, agent):
        exploration = np.log(agent.t + 1) / agent.action_attempts
        exploration[np.isnan(exploration)] = 0
        exploration = np.power(exploration, 1 / self.c)

        q = agent.value_estimates + exploration
        action = np.argmax(q)
        check = np.where(q == q[action])[0]
        if len(check) == 1:
            return action
        else:
            return np.random.choice(check)


class SoftmaxPolicy(Policy):
    """
    The Softmax policy converts the estimated arm rewards into probabilities
    then randomly samples from the resultant distribution. This policy is
    primarily employed by the Gradient Agent for learning relative preferences.
    """

    def __str__(self):
        return "SM"

    def choose(self, agent):
        a = agent.value_estimates
        pi = np.exp(a) / np.sum(np.exp(a))
        cdf = np.cumsum(pi)
        s = np.random.random()
        return np.where(s < cdf)[0][0]


class FrequentistPolicy(Policy):
    """
    Frequentist policy used a fixed length for pure exploration then the rest for pure exploitation
    """

    def __str__(self):
        return "Freq"

    def __init__(self, n):
        self.N = n
        self.n = 0
        self._last_choice = None
        self._optimal_choice = None

    def choose(self, agent):
        if self.n < self.N:
            if self._last_choice is None:
                this_choice = 0
            else:
                # absolute even distribution
                this_choice = (
                    self._last_choice + 1
                    if self._last_choice != max(agent.value_estimates.shape)
                    else 0
                )
            return this_choice
        elif self.n == self.N:
            # not really a t-test. It saves the trouble of indecision. The intuition still holds
            self._optimal_choice = np.argmax(agent.value_estimates)
            return self._optimal_choice
        else:
            return self._optimal_choice
