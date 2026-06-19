# Tech Stack learnings

> Source: Notion page "Tech Stack learnings" — https://app.notion.com/p/383ef141e3578075877ddce691641166
> Exported: 2026-06-19

### Next.js
A full-stack React framework optimized for the frontend, user experience, and search engine optimization (SEO) through server-side rendering (SSR).

### Express.js
Backend

### Postgresql
Database

#### MassiveJS ORM
You got classes (inheritance/polymorphism yapyap) in ur code and then you got rows and columns in ur database. How to transfer lol
ORM tries to bridge that gap.
Traditional ORMs like sequelize try to abstract it too much so its hard to control but massivejs tries to keep it as similar to normal postgres
MassiveJS:
1. You can write SQL as functions that you can call anywhere
2. Creates an interface in ur code for u to access ur database tables db.users.find({id: 1})
All you need to do is learn SQL

### AWS

### Redis

### **Workflow & Queues**
- BullMQ — Redis-backed job queue
  - You have heavy workload stuff you need to do, but you dw wait till they are done before user sees "success". So just put them in the job queue (bullmq), and you can basically consider them done.
    - Producer - the api service. It will drop a payload into the message queue then walk away
    - Consumer - it constantly polls the queue for work, then picks up the payload then does the grunt work, then repeat (slave)
    - The queue - in redis so it is persistent and fast (in-memory data structure)
  - The queue abstracts a few things for you so you can be rest assured that the job WILL be done eventually (and quickly)
    - Persistence (redis stuff HAHA)
    - Retries - if some consumer fails, it will automatically and exponentially retry (1s, 2s, 4s, 8s, etc)
    - Concurrency - You can have 10 different workers, bullmq ensures atomicity so one worker only picks up one job at a time.
    - You can delay the job also if uw??
- Windmill — workflow orchestration platform
  - So suppose you have 5 different tasks that need to be done where A depends on B and so on.
  - Instead of code doing them one by one and then having code for if A fails what to do etc, windmill treats them as a DAG and does it for you
    - You create nodes (the code scripts)
    - Use windmill UI to connect the nodes into a DAG
    - Abstract the rest to windmill to ensure it finishes it lol
- Socket.IO — real-time communication
  - Websockets lol - instead of constantly polling, just create a websocket that is constantly persistent so they can alw talk to one another no problem

```javascript
const { Server } = require("socket.io");
const io = new Server(3000);
```

```javascript
io.on("connection", (socket) => {
console.log("A user connected:", socket.id);
```

```javascript
// You can listen for specific events from the client
socket.on("join-room", (userId) => {
socket.join(userId); // Join a room specific to this user
});
});
```

### **Data & Analytics**
- ClickHouse — OLAP/analytics queries
- Snowflake — data warehouse
- OpenSearch — search engine
- AlaSQL — in-memory SQL for lightweight operations

### HTTP & Utilities
- Knex (query builder alongside MassiveJS)
- Axios + cache adapter
- Puppeteer (headless browser/PDF gen)
