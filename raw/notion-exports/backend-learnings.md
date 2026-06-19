# Backend learnings

> Source: Notion page "Backend learnings" — https://app.notion.com/p/37bef141e357809cb9b8db0f9b916bf3
> Exported: 2026-06-19

So it starts with a server, and a user talking to a server. Suddenly, the server dies! The server restarts, but all of the users data is gone :( . So then they created databases!!!! Store all that data in that bitch. Now, user happy.
Suddenly, there are many users. User complainnnn. Server sloww. Never respond fast enough. So server create many versions of itself to handle responses concurrently (horizontal scaling). Now many user can talk to all the different servers to get their job done. User happy!
But wait, now when user sends a request, which server should it pick (since there are many). Introducing, load balancer. Load balancer sits in between user and request. It takes the user request, does different algorithms (round robin etc), then chooses which server is best for the user.
Now we want to do more decoupling. I want to split the individual functions (the code) from the servers. So we create microservices architecture (this is the breaking point of society)

**The Participants**

| Term | Definition |
|------|------------|
| Client | Anything that sends a request — a browser, a mobile app, or even another server |
| Server | A machine that sits and waits for requests, does work, and sends back a response |
| Browser | A specific type of client that humans use — it also renders HTML/CSS/JS into a visual page |

**Addressing**

| Term | Definition |
|------|------------|
| IP Address | The real numerical address of a machine on the internet (e.g. `142.250.80.46`) |
| Domain | The human-readable name that maps to an IP address (e.g. `google.com`) |
| DNS | The phone book that translates a domain name into its actual IP address |
| Port | A numbered door on a server — one machine can run many services, each on a different port. HTTP uses 80, HTTPS uses 443 |
| Localhost | Your own machine. `localhost:3000` means "a server running on my own computer on port 3000" |
| URL | The full address of a specific resource — protocol + domain + port + path |
| Origin | Protocol + domain + port combined (`https://api.com:443`) — this is what CORS compares |
| Endpoint | A specific path on a server that does something (`/login`, `/users/:id`) |

**The Conversation**

| Term | Definition |
|------|------------|
| HTTP | The agreed-upon language/format that clients and servers use to talk to each other |
| HTTPS | HTTP but with TLS wrapped around it — the conversation is encrypted in transit |
| Request | The message a client sends to a server asking for something |
| Response | The message the server sends back |
| Header | Metadata attached to a request or response — info about the message rather than the message itself (e.g. `Content-Type`, `Authorization`) |
| Body | The actual data payload of a request or response |
| JSON | The standard format for structuring data sent between client and server |

**HTTP Methods**

| Term | Definition |
|------|------------|
| GET | Fetch data — no body sent, just asking for something |
| POST | Send data to create something new |
| PUT | Replace an existing resource entirely |
| PATCH | Partially update an existing resource |
| DELETE | Remove a resource |

**Storage**

| Term | Definition |
|------|------------|
| Cookie | A small value the server tells the browser to store — browser automatically attaches it to every matching request |
| localStorage | Browser-side storage that JavaScript can freely read and write — unlike HttpOnly cookies |
| Session | A server-side record of a logged-in user, identified by a session ID stored in a cookie |

**Status Codes**

| Code | Definition |
|------|------------|
| 200 | Success |
| 201 | Successfully created something |
| 400 | Bad request — client sent something malformed |
| 401 | Not authenticated — server doesn't know who you are |
| 403 | Authenticated but not authorized — server knows who you are but you don't have permission |
| 404 | Resource not found |
| 500 | Server crashed — the server's fault, not yours |

### Networking
TLS bla bla bla

### Object storage
S3 - Store all your big ahh files and videos and nonsense in there, its like a giant bucket but with O(1) retrieval. Its highly optimised (somehow)

### Load balancers
So you have a lot of servers now, but how do you decide which server to send that users request to? Load Balancer! Load balancer sits in between user and request. It takes the user request, does different algorithms (round robin etc), which then chooses which server is best for the user. Then it sends the request to the server.

#### Algorithms:
1. Round-robin algorithm: Each request goes one-by-one to all the servers
2. Weighted round-robin: Same thing, but each request has an associated weight so proportionately send servers
3. Weighted least connections: Sees the server with the fewest incoming connections and then routes it to that server, but weighted so larger servers can handle more connections.

Sticky sessions are a thing as well, where if one user initially gets allocated to server B, the load balancer will try so that the next time also they will get server B.

### Microservices
So we have a bunch of servers and a load balancer. But our server code is still one giant, heavy block. If a junior developer makes a typo in the video upload code and crashes the server, the payment system goes down too. Everyone loses their mind.
So we do more decoupling! We chop that giant server into tiny, independent servers called **Microservices**. One server only does payments. One only does video processing. One only does analytics. Now if the video server crashes, people can still buy stuff.
Microservices: Decoupled giant monolithic server into specialized pieces (payments, video, analytics). Everyone happy!

### API Gateway

### Event brokers
Now you got all this microservices, and s3 wants to send something to multiple microservices to make them do stuff (like uploading a file there means some other functions need to run). It directly talks to each of the microservices, but suddenly one microservice goes down. The whole
The Nightmare Scenario:
- S3 wants to send a file to multiple microservices
- Uses direct HTTP calls to everyone
- Suddenly, one microservice dies!
- Whole thing fails, data vanishes into thin air, and you have absolutely no idea which one failed
- S3 says "well I tried" and drops the request. User got ghosted lol.

So that's why, now got
Event Broker (Digital post office + shock absorber)
An abstraction layer that sits in the middle so systems don't rawdog talk to each other.
- S3 doesn't talk to the service. It drops a tiny text note ("Yo a file was uploaded") into the broker and leaves.
- Broker writes it safely to a hard drive disk (SSD).
- Buffering (Load leveling): Microservice isn't flooded. It pulls messages at its own comfortable pace (e.g. "give me 5 right now"). Protects server from being hugged to death by traffic.
- Fault Isolation: Microservice drops dead? Broker holds the mail until it comes back online. Zero data loss.
- Decoupled Routing (Fan-out): S3 doesn't know or care who is listening. Add a new analytics service next month? Don't rewrite S3 code, just tell the new service to listen to the broker.

**Architecture**
Message Broker vs Event Broker:

Message Broker (e.g. RabbitMQ, AWS SQS)
- Optimised for Commands ("Do this" like send email)
- Destructive queue: Consumer pulls it out, processes it, broker shreds it forever. Once it's read, it's gone.
- Transient retention.

Event Broker (e.g. Apache Kafka, AWS Kinesis)
- Optimised for Facts ("This happened" like order completed)
- Log append-only stream: Written sequentially to disk. Consumer reads it but event stays on disk.
- Consumer just moves its own pointer (offset).
- You can rewind time to replay past events if your database gets corrupted by a bug. Literal time machine.

AWS Deconstructed Architecture
- Traditional brokers (RabbitMQ/Kafka) do routing (brain) and buffering (muscle) in one shot.
- AWS abstracts that further dumb ass to give you serverless pricing:
- Amazon SQS: The buffer/mailbox. Completely dumb, zero routing intelligence, just holds messages safely.
- AWS EventBridge: The router. Inspects the actual JSON payload, does content-based filtering, and drops copies into the right SQS queues.

Extra Broker Superpowers (Middleware features)
- Strict Ordering: FIFO queues using sequence numbers so Event B never happens before Event A.
- Payload Transformation: Strips out 498 lines of junk from a 500-line webhook before handing it to the service.
- Schema Validation: Checks JSON text against strict schema (Protobuf/Avro). Throws error at producer if field names are wrong. Type safety over the network!
- Automatic Retries: Exponential backoff (waits 5s, 10s, 30s) if database blinks offline. No messy try/catch/sleep loops in your code.
- Dead Letter Queues (DLQ): Quarantines "poison pill" messages into a separate folder so it doesn't block the line. Engineers inspect it later.

### Auth
Auth tries to solve two problems

**1. Authentication:**
How you verify the username and password is correct.
1. User sends email and pw (or smth like that)
2. Server checks the DB by email and it gets back some stored hash (big ahh random string)
3. Server runs bcrypt.compare(pw, stored hash) (basically encrypt the inputted pw and check if its the same as the hash)
4. If false, deny access, if true, youre in boi
5. If true, then you also issue access token and refresh token (this is useful for the next step)

But if theres just this, then you have to look at db every time for every single request, since the server would have no idea who the request came from
And thats so lame fr, so they introduced:

**Persistent authentication**
So now u want it so that when user sends another req, they have some receipt that says "sup bro i alr logged in here b4 let me come in again cuh" so that u dont needa look at the db again and again
So the normal way is that you store the username and password in the database(using bcrypt), then when username comes, check the database, create a session object and store it in cache, give browser the session id that it attatches as a cookie for future requests.
But then this is stateful auth, you have to store every active session and the server has to remember you (lame).

**JWT: JSON Web Token**
Now you just attach the user identity and stuff into a token (jwt) so the server can verify the token and then check if u is good. JWT has three parts:
1. Header: The algo used to sign number 3
2. Payload: The user data (userid, role etc etc)
3. Signature: The cryptographic hash the server computed (it uses a secret key only the server knows)

How it works:
1. If its the first time logging in with username and pw, do normal auth, then give the access token (jwt) and the refresh token.
   1. Access token is only for 15 mins and is the receipt (stored in like memory or local storage)
   2. Refresh token lasts like 30 days and is used to keep generating access tokens (stored for browser in somewhere secure like "HttpOnly")
      1. HttpOnly is some flag in a cookie that has the rule that javascript cannot read the cookie
      2. For the server it will also store that refresh token in some db and you want it to be some random ahh string that u cant actually use to login so that you can delete it and force a logout if u want to
2. Client now attaches the access token to their header `Authorization: Bearer <token>`
3. Client sends another req to server, server sees the access token(jwt) then the middleware uses jwt.verify(token, SECRET_KEY) to recompute the signature and check expiry. If allz good then allz good.
4. If the access token is expired or doesnt work, the server throws an error.
5. Then the browser is like wtf bitch then it sends a req for the refresh token to some endpoint like api/refresh or sm shi (it attaches all the cookies in the domain)
6. Server checks database for the refresh token, if it exists then give them another access token (call the function jwt.sign() again).
7. Client gets to log in and swap the access token for a new one

If the refresh token expires as well, then they have to do the login page again (wasted)

**Auth0/Amazon cognito (user pools):**
Outsource the entire auth to them lol. When user sends req now it goes like
Login:          User → Auth0 (credential check, issues tokens) → User gets tokens
Every request:  User → YOUR server (verifies token locally using Auth0's public key). Auth0 is not involved at all

```javascript
const checkJwt = auth({
audience: 'https://your-api.com',        // must match what you set in Auth0 dashboard
issuerBaseURL: 'https://your-tenant.auth0.com/', // your Auth0 tenant URL
});
```

**Authorization**
Basically just role based access, you have logic somewhere in ur middleware to see what permissions that user should be able to see then gate them from the stuff they cant see based on their permissions lol

### TLS

### Throttling / Rate-limiting
Rate limiting - set a max number of requests a user can make within a specific time window (eg 100 req/min) - if exceed give like error code 429
Throttling - Make sure the requests are processed over time so that traffic flows steadily by buffering, queuing or delaying them.

### CORS
By default in the past, the internet had the same origin policy, one origin (like https://localhost:3000) cant fetch from another origin (https://localhost:4000). But now, we have frontend in one origin like myfrontend.com and then backend is another origin (like api.com) but they two need to talk now. But currently they get blocked
So CORS is a system where a bunch of http headers are passed between the browser and server so the backend can bypass that rule for trusted origins.
So now when your frontend sends a request to your backend (api.com), it will see that:
1. It does not know what api.com is
2. It will send a OPTIONS request to that backend and the backend will reply if it permits cross origin sharing from the frontend
3. The backend will return the specific CORS headers to the frontend, which the frontend then uses to talk to the backend
4. Backend then allows the real frontend request to send

### Router

### Handlers/Controllers

### Cache
So querying ur database everytime is lowkirkenuinely hella slow and like latency boohoo.
Redis lol - key-value storage inside your RAM (cos ram is faster). It is in-memory (the servers RAM)
**TTL** - Time to Live: How long that shi stays in redis

**How it works:**
**Cache-aside (reading from db):**
1. Some mofo requests ur server. It passes api gateway and load balancer then hits ur controller
2. Controller looks at shared model and then queries redis first, two things:
   1. Cache-hit: Shared model gives the JSON back to controller who then immediately sends to user.
   2. Cache-miss: Shared model fail so then controller continues on the long ahh quest to query the database. Once it queries the database, shared model again executes a background command to save that data into redis with a TTL

**Writing to DB**
Write-through:
1. User sends a write req to db
2. Write to redis (redis blocks)
3. Redis writes to DB (send success)
Safe, success is only shown once it writes to db. But slower for user

Write-behind:
1. User sends a write req
2. Write to redis (send success)
3. Concurrently redis writes to DB
Risky, if redis writing to db failed then data vanishes into thin air.

Write-around:
1. Just write straight to the db dont care abt redis LOL

**Problems**:
1. Stale data: Now u got two separate places where data stays (redis + db). DB data can change but it doesnt get updated to redis. So redis data becomes stale (not updated).
   1. Solution: Cache invalidation: The second some UPDATE or DELETE request hits the database, make sure it gets deleted in redis so that the next request for that data will hit
2. Cache Avalanche: If u set the TTL for all the things in the cahce at the same time with the same TTL, and suddenly they all expire, ur going to suddenly get all the requests flooding ur database at the same second since everything becomes a cache miss:
   1. Solution: Jitter (Randomised TTL) - Add a random variance to TTL.
3. Cache Stampede: Super popular data target, suddenly their cache key expires and 5000 concurrent requests come for that data. All of them end up querying the DB instead of one req querying the db while the rest wait for it in redis
   1. Solution: Mutex lock(Distributed locking) - When a data target (key) gets queried, add a lock for that key (with a expiration time). Then when other requests get a cache miss but see that lock, they wait for a bit first
4. Cache Penetration: Some hacker wanna DDoS or smth and sends a million requests for something that doesnt exist - all of them cache miss and hit ur database lol. But since it doesnt exist it never gets written to redis.
   1. Cache the null: If database returns null for a key - cache it as well (but with a short TTL)
   2. **Bloom filter**: Used to confirm if something is definitely not in a database. A massive array of 0's and 1's with k hashing algorithms, run through the key through all the hashing algorithms then flip the corresponding 0's to 1's based on what the algorithms output. False positives could happen (cause like other keys could coincidentally flip all the exact ones that ur key flips), so its a randomised data structure :o

**Eviction Policies:**
RAM is expensive and small compared to SSD, so ofc theres a limit to how much data you can have in RAM, so you gotta clean up the stuff in cache:
1. LRU (2040 pls im scared)
2. LFU (least frequently used)
3. Volatile LRU/LFU - Keys that dont have a TTL persist there forever
4. No-eviction: Just dont delete anyth and when RAM fills up just boohoo and reject and wait for some TTL to expire or smth

Cache is good:
1. Reading the db a lot more than writing (ofc)
2. Dont care so much abt stale data (like dont cache account balance lol)
3. If ur database is too small (redis extra latency is more than just querying ur db normally lol)
4. Dont cache super specific unique queries (ofc)

CDN Caching:
Dont need to let the req travel through load balancer api gateway bla bla just to hit cache when u can put the cache outside of it

### Pub/sub

### Event routing
- A route starts from the user clicking something causing the frontend to make a request to the backend → AWS load balancer sends that request to the right server (region) with least load → express server then has middleware that does 1) authentication (auth0 check if JWT token is valid), 2) authorization, 3) rate limit to check for spamming 4) check if MFA required. → express router to route it to the right function → controller to call the actual logic (shared model)
- The router routes the request to the right handler and then the handler will call the right functions from the shared model, and all the other things needed for the function to work, then send back the response to the router to send it back to the user.
- Shared Model → store all logic (like database queries and business stuff) into a single shared model to have as an internal npm package

### How different servers talk to one another:
#### API Call
Ur server wants to get smth from another server. The other server gives u an endpoint. U call that endpoint and say the stuff u wanna do to it (sus).
**REST API:** Use standard HTTP methods (GET POST etc) and then it will return JSON. There are endpoints for each specific service, and that endpoint has a fixed way of returning data back to you
**Graph QL:** You send a query that "looks" like the JSON you want to a single endpoint, and then the client will decide what exactly to give you
**GRPC:** Complex but really fast way for servers to talk to one another. Uses some binary and .proto files but both the client and server need to agree on exactly what the data is.
- Really useful for when microservices inside ur own architecture send lime millions of reqs to one another, but not so useful if ur creating an api for another developer in a diff company (REST is better)

#### Polling
But ur server wants the data constantly (so the data stays up to date). So u constantly ask the other server "are we there yet" lol
Same API type of call, but with a timer or loop and then the client will analyse the response to see if anyth changed

#### Webhook
But calling the server every so often is kinda lame, and then u have stale data in between each poll. So why not, when smth changes in the other server, that server tells u that it changed and then ur like "oh shit thanks" and update ur data.
Two things:
1. The trigger: The sender must have some logic to know which events cause something to get sent and to where (ur endpoint). The webhook emitter gets called
2. They add some auth stuff then get ready to send it to ur endpoint
3. The receiver: Receive the payload, verify the auth stuff then look at the payload
4. Return 200 so that the sender knows u got the shi

Things to note:
1. Webhook will try to send to you again if it fails (lets say ur server died or smth), so you need to make sure your payload processing is idempotent
   1. Idempotent - Idempotent describes a function that produces the same result regardless of whether it is applied once or multiple times
2. Webhooks time-out fast: Once they send u smth, they want a response back quickly or they consider that it failed and then will retry → so do ur processing in a message queue if u can

#### Websockets
But now u wanna talk to way (imagine like real-time chatting). You can try to create a two way webhook, but then u have to do that auth shit everytime so thats really slow (latency wise). Theres also cold start problems and stuff
So u create websockets, they are stateful, persistent connection between two servers (with a one time auth thing) so they can constantly send data whenever they want.
1. Its like u just send some req "UPGRADE websocket" and then the other server replies and then boom yall tight like that now??
2. Then now dont need auth each other everytime

They ping/pong one another every 30secs or smth to check if the connection is still alive and if it isnt then the server just drops it lol

Statefulness problem: **MICROSERVICESSSS** - causes another problem, since they are stateless, but the connection is stateful. Say you have 10 servers, and some client connects using a websocket.
1. It goes through the load balancer. LB picks server A. Websocket created between client and server A
2. Client sends another req using the websocket, LB routes you to server B, server B is like wtf who you bitch we dont websocket connection, rejects u (haha noob)
Solution - use the sticky sessions thing for load balancers

Now client 1 talks to server A and client 2 talks to server B, but they needa talk to one another, example:
**The Flow:**
1. Client 1 sends a "Cursor Move" event to Server A.
2. Server A needs to tell everyone else in that same document: *"Hey, Client 1 is now at position X,Y."*
3. If Client 2 is connected to Server B, server B doesnt know that shit happened, so server B still has stale info
Solution: Use a pub/sub HAHAHHA
