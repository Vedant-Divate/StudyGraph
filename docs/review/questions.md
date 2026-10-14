# Question review sheet (20 verified MCQs)

Check each: correct / ambiguous / wrong tag. Two reviewers initial.
## Q1 [easy] Definition (Sample Space)
Stem: As described in the course material, what is the sample space in a random experiment?
- A. A description of all the things that may happen during a random experiment. **KEY** (misc: - | why_wrong: -)
- B. An arbitrary list of outcomes with no need for formal description.  (misc: 2214aaf0 | why_wrong: The formal description of the sample space precisely captures all possible outcomes of a random experiment, ensuring no ambiguity, rather than being mere bureaucracy.)
- C. The same as the event space, since both describe outcomes of a random experiment.  (misc: 9bc31720 | why_wrong: The sample space is the set of all possible outcomes, while the event space is a collection of subsets of outcomes to which probabilities are assigned.)
- D. A simple set that must list every possible outcome exhaustively.  (misc: 8fb99daf | why_wrong: The sample space is defined by the conceptual description of all possible outcomes of a random experiment, not merely by the act of listing them in set notation.)
Concept: Definition (Sample Space) | Sources: c6243693, a903c788, 340a4401
Explanation: The course excerpt defines the sample space as 'a description of all the things that may happen during a random experiment.' Option A directly matches this definition, while the other options reflect 
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q2 [medium] Definition (Sample Space)
Stem: According to the course framework's introduction to probabilistic models, which statement accurately defines the sample space?
- A. The sample space is the set of all possible outcomes of a random experiment, formally described as a set of outcomes. **KEY** (misc: - | why_wrong: -)
- B. The sample space is just a loose list of outcomes, since formal set notation is just bureaucracy.  (misc: 2214aaf0 | why_wrong: Formal set notation provides the rigorous structure needed to define outcomes, events, and probability laws without ambiguity.)
- C. The sample space and the event space are the same thing, as they both describe the random experiment.  (misc: 9bc31720 | why_wrong: The sample space lists all possible outcomes while the event space is a collection of subsets of outcomes to which probabilities are assigned, and they are distinct concepts.)
- D. The sample space must be written as a simple, exhaustive list of every possible outcome.  (misc: 8fb99daf | why_wrong: A sample space can be defined using set-builder notation or other formal methods, so it need not be an explicit listed set.)
Concept: Definition (Sample Space) | Sources: c6243693, a903c788, 340a4401
Explanation: The course framework defines the sample space as 'a description of all the things that may happen during a random experiment,' which is formally a set of outcomes; it is distinct from the event space 
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q3 [medium] Finite Sample Space
Stem: When rolling a fair four-sided die twice sequentially, a student claims that the sample space is {1, 2, 3, 4}, arguing that since the number of outcomes is finite, this is a valid finite sample space. Which of the following best evaluates this claim according to the course material?
- A. The sample space must consist of ordered outcomes from the two rolls, such as {(1,1), (1,2), ..., (4,4)}, totaling 16 elements, as the outcome of the first roll distinguishes the second (Excerpt 1). **KEY** (misc: - | why_wrong: -)
- B. The sample space is {1, 2, 3, 4} because these are the only possible outcomes of a single roll, and since the set is finite, it is a valid finite sample space for the experiment.  (misc: 9a4bad8c | why_wrong: A finite sample space for a multi-stage experiment must account for the sequence of outcomes across stages, not just the outcomes of one stage; the sample space reflects the combined evolutions, as shown in Excerpts 1 and 2.)
- C. The sample space is small and simple because it contains only 16 outcomes, so a tree diagram is unnecessary for this experiment.  (misc: e4f7455c | why_wrong: Even though the space is finite, the course material emphasizes that tree-based descriptions are useful for visualizing multi-stage experiments and understanding evolutions (Excerpt 2).)
- D. Since the sample space has 16 outcomes and the die is fair, all outcomes in the sample space must be equally likely.  (misc: 16bcff13 | why_wrong: The finiteness of a sample space does not guarantee equally likely outcomes; the probability law separately assigns probabilities, as discussed when computing probabilities of events (Excerpt 4).)
Concept: Finite Sample Space | Sources: fb9f0646, de6103c9, 71276d59
Explanation: The correct answer is A, as Explicitly, Excerpt 1 defines the sample space for rolling a die twice as the set of ordered outcomes with 16 elements, emphasizing that order matters (e.g., a two followed
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q4 [easy] Finite Sample Space
Stem: In the experiment of rolling a fair four-sided die twice, a student uses a tree diagram to describe the sample space. How many elements does this sample space contain?
- A. 4 outcomes, because finite means the space is small or simple.  (misc: e4f7455c | why_wrong: It incorrectly assumes the sample space size is merely the number of faces, ignoring the sequential nature of the experiment.)
- B. 8 outcomes, because finite implies equally likely outcomes.  (misc: 16bcff13 | why_wrong: It mistakes the condition of equally likely outcomes for the mere count of outcomes in the sample space.)
- C. 12 outcomes, because any finite collection of outcomes is a valid sample space.  (misc: 9a4bad8c | why_wrong: It wrongly thinks any subset of possible results can be the sample space, rather than the full set of ordered outcomes.)
- D. 16 outcomes **KEY** (misc: - | why_wrong: -)
Concept: Finite Sample Space | Sources: fb9f0646, de6103c9, 71276d59
Explanation: According to the course material, when rolling a fair four-sided die twice, the sample space consists of all ordered pairs of outcomes, totaling 4 × 4 = 16 elements, and it is a finite set. This is co
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q5 [easy] Probability Axioms
Stem: Based on the course excerpts describing the axioms of probability, which statement must be true for any valid probabilistic model?
- A. Probabilities must be non-negative and the probability of the entire sample space is 1, as these are the ground rules any legitimate probabilistic model must obey. **KEY** (misc: - | why_wrong: -)
- B. The axioms are optional guidelines rather than mandatory rules, so I can assign any real numbers as probabilities as long as they look reasonable.  (misc: b09fc1ab | why_wrong: The axioms are consistency properties that any legitimate probabilistic model must obey, not optional suggestions.)
- C. Finite additivity applies to infinitely many events without modification, so I can sum probabilities of any collection of events regardless of whether they are disjoint.  (misc: 23d57f8a | why_wrong: Finite additivity is specifically for disjoint events; extending it to infinite collections requires additional conditions like countable additivity, which is not guaranteed by the finite axiom.)
- D. The normalization axiom requires all outcomes to have equal probability, so I only need to ensure each outcome is equally likely.  (misc: 0fbb2b4a | why_wrong: Normalization only requires the total probability to sum to 1; outcomes need not be equally likely, as long as the probabilities obey the axioms.)
Concept: Probability Axioms | Sources: 76fba4ff, 5ba88382, 8d886e84
Explanation: The probability axioms—non-negativity, normalization, and finite additivity—are mandatory consistency rules, not optional guidelines. Non-negativity ensures probabilities are between 0 and 1; normaliz
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q6 [medium] Sample Space
Stem: Consider the random experiment of rolling a standard, fair six-sided die and observing the number on top. Which of the following correctly describes the sample space for this experiment?
- A. The sample space is {1, 2, 3, 4, 5, 6}. This set is mutually exclusive and collectively exhaustive, satisfying the requirements for a valid sample space regardless of the die's fairness. **KEY** (misc: - | why_wrong: -)
- B. The sample space is {1, 2, 3, 4, 5, 6, 'even'}, because the outcome 'even' is a meaningful category that depends on what was observed during the roll.  (misc: 14c28d67 | why_wrong: A sample space must be defined before the experiment and list all possible individual outcomes, not categories derived from observed results.)
- C. Since all outcomes of a fair die roll are equally likely, the sample space must be {1, 2, 3, 4, 5, 6} with each having probability 1/6; including any other outcomes would violate the requirement that all outcomes are equally likely.  (misc: 8149927f | why_wrong: The sample space is about the set of possible outcomes, not about their probabilities; outcomes can be equally likely or not, but the sample space definition does not depend on that.)
- D. Only the numbers 1 through 6 can be observed on a die, so the sample space is {1, 2, 3, 4, 5, 6} and cannot include abstract concepts like 'even' or 'prime'.  (misc: 4d70a47c | why_wrong: The sample space includes all mathematically possible outcomes for the experiment, which may include concepts not directly observable in a single trial but are well-defined relative to the experiment's rules.)
Concept: Sample Space | Sources: d45530a9, 74fbdc6c, 4a9c59a5
Explanation: The sample space is defined as the set of all possible outcomes of a random experiment, and must be both mutually exclusive and collectively exhaustive (Excerpts 3 & 4). Option A correctly identifies 
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q7 [medium] Countably Infinite Sample Space
Stem: Based on the course material regarding probabilistic models and sample spaces, which statement correctly evaluates a countably infinite sample space where each positive integer n is assigned probability P(n) = 2^{-n}?
- A. The distribution is valid because the probabilities are mutually exclusive and collectively exhaustive, and their sum equals 1, demonstrating that countably infinite sample spaces can have non-uniform probability laws. **KEY** (misc: - | why_wrong: -)
- B. Countably infinite sample spaces cannot have valid probability distributions because there are infinitely many outcomes.  (misc: 19960e08 | why_wrong: Infinite outcomes prevent the probabilities from summing to 1, even if each term approaches zero.)
- C. All outcomes in the sample space must have equal probability since the experiment is symmetric.  (misc: 6be50250 | why_wrong: The course material emphasizes that probability laws are defined by the modeler's beliefs about likelihood, not by a requirement of equal outcomes.)
- D. Countably infinite and uncountably infinite sample spaces are treated the same way, so this distribution is invalid for the same reasons as uncountable spaces.  (misc: 30bcb955 | why_wrong: The course distinguishes between countable and uncountable sample spaces; countable ones allow direct probability assignments to individual outcomes that sum to 1.)
Concept: Countably Infinite Sample Space | Sources: d45530a9, 4a9c59a5, 371293d3
Explanation: The correct answer is A because the course material establishes that a sample space must be mutually exclusive and collectively exhaustive, and a probability law describes the modeler's beliefs about 
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q8 [medium] Mutually Exclusive Outcomes
Stem: A student rolls a fair six-sided die once and defines outcome X as 'rolling a 2' and outcome Y as 'rolling a 5'. Based on the course explanation that 'mutually exclusive means that if this happens, then that cannot happen' and that 'at the end of the experiment, you should be able to point out to me just exactly one of these outcomes', which statement correctly applies the concept of mutually exclusive outcomes?
- A. Since rolling a 2 and rolling a 5 cannot both occur on a single roll, these outcomes are mutually exclusive, and they are also collectively exhaustive because one of them must happen.  (misc: 04c49f68 | why_wrong: Mutually exclusive means the outcomes cannot both occur, but collectively exhaustive means one of all possible outcomes in the experiment must occur, so the two concepts are distinct.)
- B. Since rolling a 2 and rolling a 5 cannot both occur on a single roll, these outcomes are mutually exclusive, and the occurrence of one does not affect the other, so they are independent.  (misc: 67d7a20d | why_wrong: If two outcomes are mutually exclusive and both have positive probability, the occurrence of one precludes the other, making them dependent rather than independent.)
- C. Since rolling a 2 and rolling a 5 cannot both occur on a single roll, the probability of rolling a 2 or a 5 is simply the sum of their individual probabilities, 1/6 + 1/6 = 1/3.  (misc: 9d8cea7c | why_wrong: The addition rule for probabilities applies only when outcomes are mutually exclusive; the word 'always' incorrectly suggests it applies without verifying that condition.)
- D. Since rolling a 2 and rolling a 5 cannot both occur on a single roll, these outcomes are mutually exclusive, meaning that if one happens, the other cannot, and at the end of the experiment exactly one of the possible outcomes from the full sample space will be the result. **KEY** (misc: - | why_wrong: -)
Concept: Mutually Exclusive Outcomes | Sources: cbb81ab2, 77e5e604
Explanation: The correct answer is D, which directly reflects the course definition: mutually exclusive outcomes cannot occur simultaneously, and in any single experiment exactly one outcome is observed. Option A 
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q9 [easy] Mutually Exclusive Outcomes
Stem: According to the course excerpt, which statement correctly describes mutually exclusive outcomes?
- A. If outcome A occurs, outcome B cannot occur. **KEY** (misc: - | why_wrong: -)
- B. Mutually exclusive outcomes are also independent, meaning the occurrence of one does not affect the probability of the other.  (misc: 67d7a20d | why_wrong: Independence allows both outcomes to occur together, but mutually exclusive outcomes cannot both occur by definition.)
- C. Mutually exclusive outcomes must collectively exhaust all possible outcomes of the experiment.  (misc: 04c49f68 | why_wrong: Mutually exclusive outcomes can be a subset of the sample space without covering every possible outcome.)
- D. The probabilities of mutually exclusive outcomes can always be simply added together to find the total probability.  (misc: 9d8cea7c | why_wrong: This only applies when the outcomes are mutually exclusive and collectively exhaustive; otherwise, simply adding may misrepresent the total probability.)
Concept: Mutually Exclusive Outcomes | Sources: cbb81ab2, 77e5e604
Explanation: The course excerpt defines mutually exclusive outcomes as: 'if this happens, then that cannot happen.' Option A directly reflects this definition. The distractors represent common student misconceptio
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q10 [easy] Countably Infinite Sample Space
Stem: When defining a probability law for a countably infinite sample space such as the positive integers, which principle does the course emphasize regarding the assignment of probabilities?
- A. All outcomes must have equal probability  (misc: 6be50250 | why_wrong: The course explains that probability laws can assign different probabilities to outcomes, as illustrated by P(n)=2^{-n} for countably infinite spaces.)
- B. Countably infinite sample spaces cannot have valid probability distributions  (misc: 19960e08 | why_wrong: The course provides P(n)=2^{-n} as a valid probability distribution over a countably infinite sample space.)
- C. The probability law allows outcomes to have different probabilities, reflecting beliefs about which are more likely, such as assigning higher probability to some outcomes over others **KEY** (misc: - | why_wrong: -)
- D. Countably infinite and uncountably infinite sample spaces are treated the same way  (misc: 30bcb955 | why_wrong: The course shows that sample space setup depends on the experiment's context, as with the coin-flip example where adding weather changes the sample space details.)
Concept: Countably Infinite Sample Space | Sources: d45530a9, 4a9c59a5, 371293d3
Explanation: The correct answer aligns with the course's statement that a probability law describes our beliefs about which outcomes are more likely to occur compared to other outcomes (excerpt [d45530a9]), permit
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q11 [Easy] Collectively Exhaustive Outcomes
Stem: Based on the excerpt, if an experiment has stages and the overall outcome is created by combining results from each stage, which statement correctly identifies collectively exhaustive outcomes?
- A. A collection of overall outcomes from the experiment that together cover the entire sample space, formed by combining stage results as described in the excerpt. **KEY** (misc: - | why_wrong: -)
- B. Since the outcomes are collectively exhaustive, they must be mutually exclusive and cannot happen at the same time.  (misc: 2fd90475 | why_wrong: Collectively exhaustive only requires covering the sample space, not excluding overlaps.)
- C. Any set of outcomes that appears to cover the sample space is collectively exhaustive, even if it misses some outcomes.  (misc: 683b05c6 | why_wrong: A set must actually cover the entire sample space, not just seem to.)
- D. If the outcomes are collectively exhaustive, then their probabilities must sum to 1.  (misc: bdbe9e0e | why_wrong: Collectively exhaustive does not guarantee that probabilities sum to 1 unless outcomes are also mutually exclusive.)
Concept: Collectively Exhaustive Outcomes | Sources: 77e5e604
Explanation: The correct answer reflects the excerpt's definition of collectively exhaustive outcomes as a collection of overall outcomes from a multi-stage experiment that together cover the entire sample space, 
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q12 [medium] Events
Stem: Consider the experiment of rolling a fair six-sided die. The sample space consists of all possible outcomes {1, 2, 3, 4, 5, 6}. According to the course definition, an "event" is a subset of the sample space, and it occurs when the outcome of the experiment is inside this subset. Which of the following statements correctly identifies an event?
- A. Rolling a 3 is an event, but rolling an odd number is not an event because events must be single outcomes, not collections of outcomes.  (misc: 3166f207 | why_wrong: Events can be any subset of the sample space, including collections of outcomes, as the course defines events as subsets of the sample space where the outcome may be inside the set.)
- B. Rolling an odd number {1,3,5} is an event because it is a subset of the sample space, and it occurs whenever the outcome falls inside this set. **KEY** (misc: - | why_wrong: -)
- C. Rolling an even number {2,4,6} is not an event because it is not a "likely" collection of outcomes; events must have high probability.  (misc: 1183e7fc | why_wrong: All subsets of the sample space are events, regardless of probability, as the course defines events as subsets of the sample space without reference to likelihood.)
- D. Rolling a 3 and the outcome '3' are the same event, since outcomes and events are interchangeable.  (misc: 7000fafa | why_wrong: An outcome is a single point while an event is a subset of the sample space so they are not interchangeable as an event occurs when the outcome is inside the set.)
Concept: Events | Sources: 74fbdc6c, a554dfe2, 53c9e708
Explanation: The course material defines events as subsets of the sample space (excerpt [a554dfe2]), where an outcome is a point and event A occurs if the outcome is inside the set (excerpt [74fbdc6c]). Events are
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q13 [medium] Definition (Events)
Stem: As emphasized in the course's lecture transparencies and recitation sessions (Excerpts [c6243693] and [2ccb8c01]), an event is defined as any subset of the sample space. Which of the following statements correctly reflects this definition?
- A. An event is any subset of the sample space. **KEY** (misc: - | why_wrong: -)
- B. The sample space itself is not considered an event.  (misc: c0507237 | why_wrong: The sample space is the complete set of outcomes and is classified as an event in the definition.)
- C. The empty set cannot be an event because it contains no outcomes.  (misc: f04421b3 | why_wrong: The empty set is a valid subset of the sample space and is therefore an event.)
- D. For an event to be valid, its outcomes must be equally likely.  (misc: 222e5bd4 | why_wrong: The definition of an event depends only on set membership in the sample space, not on likelihood.)
Concept: Definition (Events) | Sources: 518b7094, c6243693, 2ccb8c01
Explanation: The correct definition aligns with the course's formal introduction of probability concepts in lectures and their review in recitations (Excerpts [c6243693] and [2ccb8c01]), where problem-solving and 
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q14 [medium] Mutually Exclusive Events
Stem: According to the course excerpts, if two events A and B are mutually exclusive, which statement correctly describes their intersection and the outcome of the experiment?
- A. The intersection of A and B is the empty set, and the experiment results in exactly one of the two outcomes occurring, consistent with mutually exclusive events. **KEY** (misc: - | why_wrong: -)
- B. Mutually exclusive events are independent, so the occurrence of A does not affect the probability of B.  (misc: 4c2e2df5 | why_wrong: Independence requires that knowing one event occurred gives no information about the other, but mutually exclusive events cannot both occur, so knowing one occurred makes the other impossible.)
- C. If events are mutually exclusive, their probabilities must sum to 1.  (misc: 2a3bce6d | why_wrong: Probabilities sum to 1 only if the events are also collectively exhaustive, which is not guaranteed by mutual exclusivity alone.)
- D. Mutually exclusive events cannot overlap in Venn diagrams, so their circles must be completely separate.  (misc: aa9e9987 | why_wrong: Venn diagram representation shows mutually exclusive events as non-overlapping circles, but the defining feature is that their intersection is the empty set, not their physical placement in the diagram.)
Concept: Mutually Exclusive Events | Sources: cbb81ab2, f624af14, 65d58544
Explanation: The course excerpts define mutually exclusive events as those where 'if this happens, then that cannot happen' and where outcomes have 'no common elements' (excerpt 4). This means their intersection i
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q15 [medium] Collectively Exhaustive Outcomes
Stem: As described in the course excerpt, the overall outcome of a multi-stage experiment is formed by combining the results from each stage (e.g., '2, 3' represents the result of Stage 1 and Stage 2). Given this, a collection of overall outcomes is collectively exhaustive only if it covers the entire sample space of all possible combined outcomes. Which of the following statements correctly reflects this concept?
- A. A set of outcomes is collectively exhaustive if and only if the outcomes are mutually exclusive.  (misc: 2fd90475 | why_wrong: Collectively exhaustive only requires that the union of the outcomes covers the entire sample space; mutual exclusivity is a separate concept.)
- B. Any collection of outcomes that appears to cover all possibilities is collectively exhaustive, regardless of whether it actually includes every possible combined outcome from the stages.  (misc: 683b05c6 | why_wrong: A set is collectively exhaustive only if it actually includes every outcome in the sample space; seeming to cover is not sufficient.)
- C. If a collection of outcomes is collectively exhaustive, then the sum of the probabilities of the individual outcomes must equal 1.  (misc: bdbe9e0e | why_wrong: This is only true if the outcomes are also mutually exclusive; collectively exhaustive alone does not guarantee the probabilities sum to 1, as overlapping outcomes would make the sum greater than 1.)
- D. A collection of overall outcomes from the two-stage experiment is collectively exhaustive if it includes every possible ordered pair of stage results, thereby covering the entire sample space. **KEY** (misc: - | why_wrong: -)
Concept: Collectively Exhaustive Outcomes | Sources: 77e5e604
Explanation: Collectively exhaustive outcomes are defined by their union covering the entire sample space; they do not need to be mutually exclusive, a set that only 'seems' to cover is not necessarily collectivel
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q16 [medium] Events as Subsets
Stem: In the 'events as subsets' framework described in class, if a single outcome ω belongs to both event A and event B (i.e., it is inside both subsets), which of the following correctly describes what has occurred?
- A. The outcome ω is in the union of A and B, which means both events have occurred.  (misc: 7eded1cf | why_wrong: The union of two events occurs if the outcome is in at least one of the events, not necessarily both.)
- B. The outcome ω is in the intersection of A and B, which means either one of the events occurred.  (misc: 25f91a00 | why_wrong: The intersection of two events occurs only when the outcome belongs to both events simultaneously, not just one.)
- C. The outcome ω is in the complement of A, since it belongs to B, and the events are disjoint.  (misc: c5a38ac9 | why_wrong: Disjoint and independent are not the same; disjoint events cannot occur together while independent events' occurrence does not affect the other's probability.)
- D. The outcome ω is in the intersection of A and B, meaning it has occurred in both events simultaneously. **KEY** (misc: - | why_wrong: -)
Concept: Events as Subsets | Sources: a554dfe2
Explanation: The excerpt defines events as subsets of the sample space and states that an outcome inside a subset means the corresponding event occurred. Therefore, an outcome inside both subsets A and B means it 
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q17 [medium] Collectively Exhaustive Events
Stem: According to the course excerpt on collectively exhaustive events, which statement is accurate?
- A. Collectively exhaustive events are always mutually exclusive.  (misc: 4ca0f5dc | why_wrong: The excerpt defines collectively exhaustive and mutually exclusive as distinct concepts; collectively exhaustive only requires that some outcome occurs, not that exactly one occurs.)
- B. If events are collectively exhaustive, each must have probability 1/n.  (misc: 94536284 | why_wrong: Probability assignments depend on the experiment's likelihoods, not on the events collectively covering the sample space, as the excerpt focuses on outcome coverage, not numerical chances.)
- C. Mutually exclusive and collectively exhaustive is the same as a partition.  (misc: 878f9a8a | why_wrong: The excerpt distinguishes the definitions of mutually exclusive and collectively exhaustive; a partition requires both, but not all collectively exhaustive event sets form a partition, as the excerpt explains.)
- D. Collectively exhaustive events ensure that at least one outcome from the collection occurs, regardless of whether the events overlap. **KEY** (misc: - | why_wrong: -)
Concept: Collectively Exhaustive Events | Sources: cbb81ab2, 030ee558, d33824eb
Explanation: The course excerpt defines collectively exhaustive events as those where, no matter what happens in the experiment, you're going to get one of the outcomes inside the collection, without requiring the
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q18 [medium] Complementary Events
Stem: In the cream cheese analogy from lecture, the entire sample space is a 1-pound block of cream cheese, and each event's probability is the amount of cream cheese on top of it. If event A has 0.7 pounds of cream cheese on top of it, what is the probability of the complement A'?
- A. The probability of A' is 0.3 pounds, since the total is 1 pound and A' takes the remaining portion. **KEY** (misc: - | why_wrong: -)
- B. The complement of an event is its 'opposite' in everyday language, so A' should be the opposite of A in real life, making P(A') = 0.7.  (misc: f1b9d77b | why_wrong: Everyday 'opposite' doesn't account for the total probability constraint of 1 pound of cream cheese.)
- C. The formula P(A') = 1 - P(A) only works when P(A) is neither 0 nor 1, so with P(A) = 0.7, we cannot use it and must find another way.  (misc: b3c92c3e | why_wrong: The cream cheese analogy applies regardless of P(A)'s value, as the total is always 1 pound.)
- D. The complement of an event always has lower probability than the event, so since P(A) = 0.7, P(A') must be less than 0.7.  (misc: 1e4201af | why_wrong: A' could have higher probability than A because the cream cheese portion for A' is just what's left, which could be more or less than A's portion.)
Concept: Complementary Events | Sources: 2ccb8c01, fd31ac68, 5903539b
Explanation: The cream cheese analogy models the sample space as a fixed 1-pound total, so the complement A' receives whatever portion remains after A's allocation, making P(A') = 1 - P(A). This is consistent with
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q19 [medium] Probability Assignment
Stem: According to the described process for assigning schedules, what is the probability that a randomly selected student ends up unhappy?
- A. 10%  (misc: b7b02901 | why_wrong: The initial 10% unhappy chance is modified by the resubmission step, so the final probability is not simply the initial unhappy rate.)
- B. 1% **KEY** (misc: - | why_wrong: -)
- C. 19%  (misc: 02de669a | why_wrong: Adding the initial unhappy probability (10%) and the probability of remaining unhappy after resubmission (9%) incorrectly assumes these events are mutually exclusive and can be summed.)
- D. 9%  (misc: 7c8793cf | why_wrong: The process does not treat all outcomes as equally likely; the resubmission step changes probabilities based on initial assignment.)
Concept: Probability Assignment | Sources: 8ac07a6f, a0d9935f, e871a654
Explanation: Initially 10% of students are unhappy. Of those, 90% become happy after resubmission, leaving 10% of the original unhappy group still unhappy. Thus the overall probability of a random student being un
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

## Q20 [easy] Mutually Exclusive Events
Stem: Which of the following correctly reflects the definition of mutually exclusive events as described in the course material?
- A. The events have no common elements, so their intersection is the empty set; if one occurs, the other cannot. **KEY** (misc: - | why_wrong: -)
- B. Mutually exclusive events are independent, so the occurrence of one does not affect the probability of the other.  (misc: 4c2e2df5 | why_wrong: Mutually exclusive events are dependent because if one occurs, the other's probability becomes zero, making their occurrence not independent.)
- C. If events are mutually exclusive, their probabilities always sum to 1.  (misc: 2a3bce6d | why_wrong: Mutually exclusive events' probabilities only sum to 1 if they are also collectively exhaustive; otherwise, the sum can be less than 1.)
- D. Mutually exclusive events cannot overlap in Venn diagrams, meaning they share no outcomes.  (misc: aa9e9987 | why_wrong: While mutually exclusive events have an empty intersection, Venn diagram representation is a choice; the defining feature is the empty intersection, not the visual overlap.)
Concept: Mutually Exclusive Events | Sources: cbb81ab2, f624af14, 65d58544
Explanation: The course excerpts define mutually exclusive events as having no common elements (intersection is the empty set) and state that if one occurs, the other cannot, aligning with the third axiom referenc
- [ ] correct  - [ ] ambiguous  - [ ] wrong tag  Reviewer: ____

