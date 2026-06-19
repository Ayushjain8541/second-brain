# Learnings (Internship learning log)

> Source: Notion page "Learnings" — https://app.notion.com/p/35eef141e357807cb494f1fd598d8a1f
> Exported: 2026-06-19
> Note: Weeks 1-3 below are filled in. Weeks 4-12, the monthly reflections, and the capstone section were still empty template placeholders in Notion at export time, so they are omitted here. Re-export when filled.

> Use this page daily/weekly. Keep entries short and concrete. Link to PRs, docs, tickets, and meetings where possible.

## Internship snapshot
- **Internship dates (start–end): 11th May - 31st July**
- **Team / squad:**
- **Manager:**
- **Buddy / mentor:**
- **Role focus areas:**
- **Success metrics (how I'll know I did well): Im a swe??**
- **Tools & repos I'll touch:**

## 3-month goals (north star)
1. **Goal 1: Learn everything technical**
   - Why it matters:
   - What "done" looks like:
2. **Goal 2:**
   - Why it matters:
   - What "done" looks like:
3. **Goal 3:**
   - Why it matters:
   - What "done" looks like:

## Weekly learning log

### Week 1
**Theme / focus for the week:** Introduction to the team and my project

**Top 3 outcomes shipped / contributed**
- Gained access to and learned about the tech stack with all the relevant databases
  - DBeaver - db management system (we use PG)
  - Github - momoshub repo with like 70(??!!) different repos
  - AWS - so many different systems we are using
- Learnt about a lot of different enterprise tools
  - Salesforce - used by sales to track their sales cycle
    - Lead → SQL (sales qualified lead)→ SQO (sales qualified opportunity) → closed won/lost?
    - SKU - stock keeping unit (what sales sells?)
  - Chargebee (Finance for invoices and stuff)
  - Deel (HR stuff)
  - Tableau (data for like customer success)
  - Slack - internal messaging
  - Notion - Like really good for documenting
- Interviews with key stakeholders to get pain points
  1. Interviewed so many people in the office to understand their pain points when using MASA (our internal admin platform) and SF and chargebee
  2. Learnt a lot about the standard workflows for sales teams, finance teams, customer success teams.

**Key learnings (what I now understand better)**
- Learned about the tech stack
  1. Frontend
     1. Amplify - An AWS service to manage everything frontend related
     2. Next.js/React - The core language for frontend
     3. AWS lambda serverless (sls) - to deploy functions only when triggered and then run and shutdown - useful for like scheduled tasks and one-off heavy tasks
     4. React
  2. Backend
     1. Redis - Single threaded, in memory database mainly used for cache
     2. Express
  3. Deployment
     1. Temporal: Make sure the server stays up and running for long tasks?
  4. Database:
     1. Aurora DLB - fully managed DB compatible with PG.
  5. Logging
     1. Datadog
- System design
  - It is all about tradeoffs and which thing you want to prioritise based on requirements
    - Latency - time taken for each single request
    - Thoroughput - Number of requests the server can take over time
    - Consistency - When you make something parallel, are all the parallel things in sync?
    - Availability - how available is the syste
- Git stuff
  - Git hooks (CI/CD things to add for every git push you do??)
- Claude code!!
  - How to use, functionalities and how its cracked
- Leant a lot about the CI/CD pipelines and like engineering principles for new software engineers
- Learnt about what my project is (MASA V2) - im trying to automate the workflows between the different systems like salesforce, chargebee and MASA. Anything manual or any pain point we find from the interviews, we need to consolidate and come up with solutions to put into our project.

### Week 2
**Top 3 outcomes shipped / contributed**
- PRD for our entire project (based on our interviews)
  1. After a lot of interviews and generated pain points, we prioritised what was important and solveable and we drafted our PRD for our whole project.
     1. We came up with phase 0.5 which was to streamline the upstream for the information flow to optimise everything in the future.
- ERD for the entire project (preliminary)
  1. Based on all the suggested features, come up with the suggested implementations for each of them
- More interviews done
  1. After getting phase 0.5 approval, we focused on shipping phase 0.5, doing more interviews and research to see what the product is about

**Key learnings (what I now understand better)**
- What is a PRD and ERD
  - PRD - project requirement docs (for PMs) establish stakeholders, what are their pain points what is the suggested improvements, what are the workflows you are addressing and how you are changing them
  - ERD - engineering requirement docs (for engineers) look at the suggested features, see whats the requirements (in a system design level), see whats the minimum lean build to solve the problem, propose implementation, show alternatives considered, add open questions and deployment workflows and testing.
- Learnt about the product
  - 31 different modules and features - what each of them are, some legacy and some real, what is upcoming features (ai chatbot)
- Lunch and learn
  - Memory management in Node.js architecture (???)
    - Memory leaks - memory in heap but with no pointers to it, it didnt get cleaned
  - Use like some logging method and repeatedly call the API and then track the memory using some tool((??))
- Data warehousing
  - 4 layers
    - Staging layer - where the data is stored

### Week 3
**Key learnings (what I now understand better)**
- Technical Findings
  - Did a deep dive into the codebase to try and learn fundamentals while understanding the codebase
    - A route starts from the user clicking something causing the frontend to make a request to the backend → AWS load balancer sends that request to the right server (region) with least load → express server then has middleware that does 1) authentication (auth0 check if JWT token is valid), 2) authorization, 3) rate limit to check for spamming 4) check if MFA required. → express router to route it to the right function → controller to call the actual logic
    - Shared Model → store all logic (like database queries and business stuff) into a single shared model to have as an internal npm package
    - AWS lambda functions (sls):
      - Flow: cron trigger (aws eventbridge) → aws lambda
- Lots of database learnings (understanding how databases work and everything) (see Database Learnings)
- Sent my first PR for the translator function
