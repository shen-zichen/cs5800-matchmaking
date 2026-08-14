**CS 5800 Algorithms — Final Project Proposal**

*Matchmaking in Multiplayer Online Battle Arenas: Balance versus Lane*

Team members: Zichen Shen · Liuyi Yang

# **1\. Context and Motivation**

This project started as an argument. Both of us play MOBAs — five-versus-five online battle games in which two teams of strangers, drawn from a live queue, fight across five fixed lanes — and both of us have spent years quietly resenting the invisible system that decides who we play with. We just resented different parts of it.

**Zichen — Honor of Kings.** I play Honor of Kings, a mobile MOBA. Its five lanes are fighter, jungle, mid, marksman, and support, and before a ranked game you pre-select up to two of them. What makes HoK distinctive is a hard promise: you are never assigned a lane you did not pick — you are guaranteed one of your two, and you can even pay to lock a single lane outright. Because of that promise I am essentially never stuck off-role. And yet my games often feel lopsided: one side snowballs and the match is decided in ten minutes. That contradiction is what hooked me — if the system works so hard to honor my lane, why does it seem to care so little about making the two teams evenly matched? My half of this project is the balancing side: given ten players of roughly similar skill, how do you split them into two teams that are as evenly matched as possible?

**Liuyi — League of Legends.** I have played League of Legends for seven years. League is also five-versus-five across five roles, and it sorts players by a hidden skill rating while displaying coarse tiers — Iron, Bronze, Silver, Gold, and up. Before queuing you pick a primary and a secondary role, or "Fill." My complaint is the mirror image of Zichen’s: League guards balance fiercely — it aims for a near-50% win chance on both sides — but it does not guarantee your role. Playing solo, I am regularly autofilled into a position I cannot play, and the game is lost before it begins. So my half is the lane-assignment side: out of a pool of strangers, how does the system decide who gets their chosen role and who gets sacrificed?

Arguing about this, we realized we were each fixated on a different half of the same machine — and that our two games make opposite bargains. HoK protects your lane and lets balance suffer; League protects balance and lets your lane suffer. That is not an accident; it is a design choice, and we believe we can model it.

# **2\. Clearly Defined Question**

Given a snapshot of the matchmaking queue, we model how to assemble a single fair, role-complete 5v5 match, and we study the tension between its two sub-problems: assigning players to lanes (honoring their preferences) and splitting them into two skill-balanced teams. These two sub-problems can be solved in either order, and the order encodes a philosophy. 

**lane-first** (the HoK bargain) assigns lanes first, so no one is ever off-role, then balances the resulting teams as well as possible. **balance-first** (the League bargain) splits the ten players into the most even two teams first, then assigns lanes within each team, autofilling whenever a team cannot be filled legally. Our central question is what each ordering costs. We measure two quantities — the skill gap between the two teams and the number of autofilled players — and characterize the trade-off between them: how large it is, and under what conditions it appears or disappears.

# **3\. Scope of the Project**

**What we examine.** We model the formation of one match from a static snapshot of the queue: a fixed set of players, each with a hidden skill rating (MMR) and up to two preferred lanes. Lane assignment is treated as unweighted, one-sided bipartite matching with a capacity of two per lane, using a player’s primary preference only as a tie-breaker among otherwise-equal assignments. We implement both orderings at the real match size of ten players, and we additionally measure how the matching step scales as the candidate pool grows.

**What we deliberately do not examine.** We do not model the live, online queue — players joining or cancelling, or the trade-off between match quality and waiting time. We do not drain the whole queue into many simultaneous matches (a global batch problem). We exclude weighted preferences, which would turn lane assignment into the assignment problem solved by the Hungarian algorithm, and two-sided preferences with stability (the hospital–resident matching problem); both fall outside the core textbook chapters. We also ignore within-team skill variance, balancing only average skill. Each of these is a natural extension, and we revisit them as future work.

# **4\. Relation to Textbook (CLRS) Topics**

Our three stages map onto three parts of the textbook.

**Sorting (Ch. 7).** Players are first sorted by MMR. Displayed tiers are merely coarse labels derived from MMR, so no separate bucketing is required; a sorted array together with a sliding window suffices to extract a pool of ten players whose skills are close.

**Maximum bipartite matching / max-flow (Ch. 26, §26.3).** Lane assignment is a bipartite matching between players and lanes with a lane capacity of two, solved via max-flow. The same routine serves as a feasibility oracle while the pool is being built: a saturating flow of value ten certifies that a legal match exists. Hall’s theorem explains autofill precisely — when no perfect matching exists on the preferred-lane edges, some player must be placed off-role. Because matching is polynomial, it scales, which we demonstrate as the pool grows.

**NP-completeness (Ch. 34).** Splitting ten players into two teams of minimal skill gap is the balanced-partition problem, which is NP-complete in general (reducible from PARTITION). We stress that NP-completeness classifies the problem, not our particular instance: with ten players there are only 126 distinct splits, so brute force is instantaneous. This gap is the thesis of the project — feasibility (does a role-complete match exist?) is polynomial, whereas optimization (the most balanced such match) is NP-hard, and the problem is tractable in practice only because a match is fixed at ten players.

# **5\. Weekly Plan**

The plan runs from the week after proposal approval to the presentation window. Exam 3 (Aug. 7\) is left free of project work.

| Dates | Focus | Deliverable |
| :---- | :---- | :---- |
| Jul 25 – 31 | Formalize the three-stage model on paper. Liuyi builds the matching module (max-flow with autofill triggered by Hall’s-condition failure). | Working lane-assignment demo on synthetic five-player teams. |
| Aug 1 – 6 | Zichen builds pooling (sort \+ sliding-window feasibility) and the balanced-partition module. | Pool extraction and brute-force balancer. |
| Aug 7 | Exam 3 — no project work. | — |
| Aug 8 – 11 | Integrate both orderings end-to-end. Liuyi defines the metrics (gap, autofill count); Zichen builds the synthetic-data generator. | Full pipeline producing a match from a snapshot. |
| Aug 12 – 13 | Run both orderings across preference-diversity settings; scalability test. Liuyi plots the results; Zichen writes the results section. Slides and individual videos. | Results, figures, and deck. |
| Aug 14 | Submit code and slides; present. | Final group submission. |

# **6\. Division of Labor**

The work divides along the two algorithms, matching each of us to the half we care about.

| Member | Owns | Deliverables |
| :---- | :---- | :---- |
| Liuyi | Lane assignment — bipartite matching / max-flow (Ch. 26\) and autofill via Hall’s theorem. Metric definitions and plotting. | Matching module; metric definitions; result figures. |
| Zichen | Team balancing — balanced partition and its NP-completeness reduction (Ch. 34); pooling (Ch. 7); experiment design. | Pooling and balancer; synthetic-data generator; running the experiments; results write-up. |
| Shared | Integration of the two orderings; testing, including infeasible-pool edge cases; slide deck. | One-per-group code and slides submission; each member records an individual video on their own module. |

We have deliberately kept data generation and the results write-up with one person (Zichen), because tuning the synthetic inputs and interpreting the output are tightly coupled to ensure semantic consistency across our experimental pipeline. Since our benchmark evaluates how algorithms respond to varying queue environments—such as degree of preference overlap and MMR distribution tightness—having one owner write and fine-tune the synthetic data generator allows us to efficiently explore these parametric edge cases and analyze their impact on team balance. To keep the load even, Zichen will hand Liuyi discrete sub-tasks from the data-generation and experiment work as it develops. The ownership above is distinct on paper; in practice we intend to support each other throughout.