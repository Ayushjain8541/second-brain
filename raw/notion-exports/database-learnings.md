# Database Learnings

> Source: Notion page "Database Learnings" — https://app.notion.com/p/36eef141e35780e283b7c1d30ead3c35
> Exported: 2026-06-19

### Database Design things
Data - raw data eg number/string/integer (but no context)
Information - Data but with context

#### Data Processing
Layers of processing:
1. Collection Layer : collect raw data from sources
2. Preparation Layer : validate raw data, clean it, standardise it and maybe add some stuff to it?
3. Input layer : Introducing prepared data into the system
4. Processing layer : Transform data into information through like arithmetic, comparison, sorting, summarizing, classifying and analysis
5. Output layer: Convert the internal representation to readable and then give it to user
6. Storage Layer: Store data and information in like durable media (SSD) and have indexing maybe?

You can process it either in batches (collect data over a period of time and then bam run analysis) or do it one at a time per request so real time (system design) or if ur crazy then do stream processing (for data that flows with one another?).
**Lambda architecture -** You have paths for both batches and real time
- Batch layer
- Speed layer
- Serve layer (merge both batch and speed)

#### Query processing
Layers again :
1. Parse the query (convert SQL to something?)
2. Semanticly analyse the query: Check if table exists, check permissions, and analyse the query
3. Optimisation: Optimise the query (make it efficient) based on the actual sql itself. You can mayeb choose from:
   1. Indexing: Hash table or B+-tree
   2. Caching: For data frequently accessed
   3. Parallel processing
   4. Push down optimisation: Move the processing closer to the data (?? wtf)
4. Execution plan generation: Step-by-step processing recipe (god knows)
5. Execute it (ofc lol)
6. Result (give the result)

#### Architecture
OLTP - Online Transction Processing: used for frequent small fast transactions
OLAP - optimised for like big analytical queries over massive datasets (data warehousing ooo)
HTAP - mix of both lol

**Shared-nothing architecture**
You have like many different independent nodes each having their own data (by partitioning the collective data) which is storage and they all have their own RAM and CPU which is compute. But if they want to communicate, they need their own protocols so like very expensive communication.
e.g postgreSQL, citus, MongoDB

**Shared-storage architecture**
There is a shared storage layer and they individually compute from the shared storage (decoupling storage layer and compute layer). There is some network layer in between where it somehow breaks the data in the storage layer into the compute layers??
e.g Shared storage is like s3
A whole e.g is like snowflake, aurora etc

#### Quality and integrity (lame)
**ACID:**
1. Atomicity: transaction is all or nothing (cant be like half the transaction is done, something fails and the other half doesnt happen but it still updates the first half)
2. Consistency: Transaction brings the database foward always (???)
3. Isolation: Concurrent transactions dont interfere with one another
4. Durability: Once a transaction commits, its permanent
Validation: validate type, range, reference, business rule, cross field??

#### Structured vs unstructured data
**Unstructured data**: NOT JSON
1. No schema for the data
2. Human-oriented (so its like raw visual media or audio recording)
3. The format isnt fixed
4. Implicit meaning - the information is in the content and not structure (want sentiment in a review - you have to do NLP over the review text)
For unstructured data
- store it in like a object/blob storage
- query it by either full text search or just similarity search
- Process it by other means like NLP or computer vision
- Integrate it with structured data somehow to get more insights

**Semi-structured data**: This is JSON
Some organizational properties but no strict schema
1. Structure is in the data itself
2. Flexible schema
3. Hierarchical organisation
4. Machine readable
Examples
- JSON
- XML
- YAML
- Avro, Protocol buffers, Thrift (no idea man)

**Structured data:**
I guess there like strict schema and you can index using hash and b-tree and can use SQL now. Stored in like table format where the table has a strict schema

**System design implications:**
Store unstructured in s3, semi structured in like mongoDB or postgres JSONB and structured in mysql or postgres
- This is why pg is good
If you want all types you can use like elastisearch or vector databases and data lakes (?? help)

**Monolithic:** Single large application with one central database and tightly coupled components. Scale by getting bigger servers (vertical scaling)
**Modern (Distributed microservices):** Multiple specialized services and multiple purpose specific databseses and you scale by getting more servers

#### File-based systems:
You just raw-dog the storing and like directly put the file in the storage (based).
Lots of limitations (lame):
1. Redundancy: Since the systems cant share data, theres a lot of duplications (eg customer address)
   1. Redundancy factor: How redundant it is (1 is nothing, 2 means data stored twice on average etc)
2. Inconsistency: You wanna change address, do it in every file LOL
3. If someone accesses one of the files it becomes locked and no one else can use it (haha noob)
4. Cant do concurrency (zzz)
5. No atomicity, you can have partial updates (boring)
6. You can have references in one file to deleted data in another
So thats why, there is now….

### DBMS - Data Base Management Systems
A software system that enables users and applications to define, create, maintain and control access to a database and also have mechanisms for integrity, security, concurrency and recovery (erm akshually its just an abstraction lol)
A dbms stores schemas, data types, constraints, relationships and access methods
Storage manager - manage how data is physically organised in a disk and then retrieved
Index structure - either B-tree(most common) or hash table
Buffer manager - cache layer for frequently used data
Transaction manager - maintains ACID properties during concurrent access or system failure
Recover manager - If anything fails, bring it back to before the transaction: for every transaction - log how to undo and redo

SQL is split into like 4 languages lol
1. DDL - define the schemas and stuff (CREATE, ALTER, DROP)
2. DML - manipulate the data inside the tables (SELECT, INSERT, UPDATE, DELETE)
3. DCL - control who can access the data (GRANT, REVOKE (?))
4. TCL - manage the transaction stuff (COMMIT, ROLLBACK)

### Dependencies
Functional dependency: X → Y means Y is dependent on X and X determines Y (X is determinant and Y is dependent)

### Database Snapshots

### MVCC (Multi version concurrency control)
Now imagine there are multiple concurrent programs trying to read/write/delete (transactions) the same row in the database at the same time. Intuitively, you could lock the row whenever there is a transaction and then make other transactions wait until the transaction currently using that row is done with it, but then it is really slow (L + ratio).
To solve this, some idiots created MVCC. So now everytime a transaction happens, it creates a new snapshot of the database (with a timestamp ID) that the transaction can use and modify if it wants to, while the old version is left untouched.
- Can think of this like creating a git branch of the database, where the transaction works on seperately from the old database until its over and then merges back
- But then theres the problem of merge conflicts right? There is no human to solve them, so it has the be done automatically - ie just dont merge it LOL
  - Solved by noticing that "merge conflicts" only happen in certain chained dependency scenarios
  - Eg of 2 doctors - you need et least one doctor available and currently both doctors are available, but you concurrently send a update to make both of them unavailable, but since both use a stale snapshot, it causes a conflict)

| Time | Transaction 1 (Doctor A) | Transaction 2 (Doctor B) | What the Database Tracks |
|------|--------------------------|--------------------------|--------------------------|
| Step 1 | Reads the table. (Sees A and B are Active) | | T1 has read Doctor B's row. |
| Step 2 | | Reads the table. (Sees A and B are Active) | T2 has read Doctor A's row. |
| Step 3 | Writes an update: `Doctor A = Inactive` | | First Conflict! T1 just modified a row that T2 previously read in Step 2. ➡️ Graph gets an arrow: T2 →rw T1 |
| Step 4 | | Writes an update: `Doctor B = Inactive` | Second Conflict! T2 just modified a row that T1 previously read in Step 1. ➡️ Graph gets an arrow: T1 →rw T2 |

- So you solve this by realising this situation happens by modelling it as a graph problem.
  - Edges that matter are only when one transaction has rw (read-write) dependency with another (T2 is reading data that T1 modified = T2 →rw T1)
  - Then see if there are cycles (no cycles is still fine since serializability is still preserved)
  - But how do you see whether something is a read-write transaction that is dependent on another transaction?? (why did you ask bro 😫 )
    - In the hard-disk, data is stored in tuple (those who know), and the tuple has a header
    - So make the header store a bunch of shit HAHA
      - xmin - the transaction id (t-id) that started created this tuple
      - xmax - the transaction id that will delete this tuple (if nothing yet just some default value)
      - t_ctid - the id of the new updated tuple if it was updated
    - So if u UPDATE smth in postgres it doesnt "update" it, it deletes it and inserts a new one with new appropriate xmin and xmax values
      - xmax of old one becomes the t-id
      - xmin of new one becomes t-id
    - So with all of this, when a transaction starts, you pass a snapshot object that has
      - snapshot → xmin - the lowest t-id thats still running
      - snapshot → xmax - the highest t-id assigned so far
      - snapshot → xip_list - list of t-ids that were running at the exact same time as your screenshot
    - So then when your scanning for tuples just check this:
      - Is the tuple's `xmin` committed? **If no, ignore it.**
      - Is the tuple's `xmin` newer than my snapshot's max? **If yes, ignore it (it's from the future).**
      - Is the tuple's `xmax` filled in, and did that transaction commit *before* I started? **If yes, ignore it (it's been deleted/superseded).**
    - So whenever a transaction reads a tuple and its visible, it creates a SIREAD lock and then
    - if another concurrent transaction comes along and tries to update that same row, it writes a new tuple and sets the `xmax` on the old tuple → then checks the siread lock and realises its already being used → add it to the dependency graphh
- This serialization level is serializable snapshot isolation (what mvcc uses)
