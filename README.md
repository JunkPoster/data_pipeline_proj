# Personal Project: Event Processing and Analytics Pipeline
## Overview
My goal was to create a data pipeline that produced auto-generated events, took that data, performed some transformations, generate reports, and update a database with it. 
- I originally wanted to make it real-time so that events would constantly be produced, then a consumer would take those events and actively perform transformations, but that concept became extremely complicated (for me) when factoring-in that I'm using `moto` to mock all of the AWS aspects.

I essentially restarted the majority of this project with about 8 days left in my deadline. If I had more time, I'd spend at least another week developing unit & integration tests, and beef-up the error handling in general. 

I also realize a lot of this is extremely rudimentary, but a lot of it was me learning and somewhat guessing how a real system might look.

## To Run It:
I tried my hardest to make this as seamless as possible, but I'm just not experienced enough. 
- Option 1 - GitHub: If you just want to run it as-is and have the results opened and shown, then you should be able to download the repository and open the `isolated_run.py` (assuming you have Python and PostgreSQL installed).
- Option 2 - Docker: Download this entire directory, unzip it, navigate to it in your CLI, then run `docker-compose up --build`.
    - Once finished, you can run `docker-compose down -v` to clear the volumes created for it.

You'll find the generated figures in `/figures`, and the logs in `/logs`. 

When using option 1 you should be able to run queries and such within pgAdmin under the 'localhost' database. For Option 2, you'll likely have to access it within Docker via: `docker exec -it <container_name> psql -U postgres -d datapipeline`, with the *container_name* likely being the name of your directory. If not try using `data_pipeline_project-db-1`. 

> **PostgreSQL**: You will need to enter your actual PostgreSQL local password into the `.env` file in order for it to properly utilize a local database. If you'd rather not do that, you can instead change the password to your 'postgres' profile to '`your-password`' (literally 'your-password').
> *Windows*: `psql -U postgres` -> `ALTER USER postgres WITH PASSWORD 'your-password'`.
> *Linux*: `sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'your-password'`.


# The Dataset
## The Base tables
The base dataset consists of 5 tables containing data that's regenerated at the beginning of each run, using the `constants\psql_constants.py` and the `src\psql_client.py` files:
- `companies`: Contains a list of example companies (Netflix, Amazon, Google, etc.), which bid in auctions to win ad space.
- `devices`: This is used to identify the type of device the ad will be occupying, and what the user is using. 
	- Contains various `device_type`'s, such as: `mobile`, `desktop`, `tablet`, `smart_tv`, `gaming_console`. 
- `ads`: Hosts the individual ads created by each company, which will be assigned to an auction when it's won.
	- Holds `ad_type` (video, banner, native, etc.), and `ad_category` (sports, technology, finance, etc.).
	- Has a *foreign key* `company_id`, from the `companies` table.
- `auctions`: Contains the fake auctions that have taken place.
	- `bid_amount` is the amount that won the auction
	- *Foreign keys*:
		- `ad_id` from `ads`.
		- `company_id` from `companies`.
		- `device_id` from `devices`.
- `users`: Using the *Faker* package, users are randomly generated on each run. They're tied to the `events` table when they interact with an ad. Their name, email, and phone number are all randomly generated.


## The `raw_events` Table
After those tables are created and filled with generated data, the `producer_script.py` is used to generate a number of fake events, and send them to a mock Kinesis Data Stream. The `consumer_script.py` then reads from that stream and stores those events into an S3 Bucket and the `raw_events` PostgreSQL table. These events essentially act as the interactions that users have with the fake ads, and it helps tie together the various cogs in the machine.
- **Note**: I actually store the generated events into the PostgreSQL server first, then read it from that table and load that into the S3 so it'd properly generate the `event_id` column (I'm still pretty new to this, so I'm sure there's an easier, more efficient way).
- The `event_type` is randomly selected between a list of interactions I thought would make sense for ads: *impression, click, conversion, hover, view, like,* and *share*. 
	- **Note**: I actually considered making this a dict, and assigning each interaction its own arbitrary "value", and then using that metric to generate all kinds of trends and such (*i.e. an 'interaction' would be more valuable than just a 'view'*).
- The `metadata` contains some extra information about the user, like their *browser*, and *IP address* (all simulated by the *Faker* package).
- *Foreign keys*:
	- `user_id` from `users`.
	- `ad_id` from `ads`.
	- `company_id` from `companies`.
	- `auction_id` from `auctions`.
	- `device_id` from `devices`.

When querying the `raw_events` table from within pgAdmin:
![image](https://github.com/user-attachments/assets/ac96d244-1346-4bd0-9425-e0ace0c48249)


## The `processed_events` Table
Our `transformer.py` script takes the raw data from the S3 Bucket and begins processing it. This is done in a few different ways (detailed later), and it then stores that data into a different S3 Bucket and PostgreSQL table, `processed_events`.
Querying `processed_events` in pgAdmin:
![image](https://github.com/user-attachments/assets/38ac23f4-faa0-42d4-a8bb-217bd10e98af)


## Database ERD Model (PostgreSQL)
The blue tables are generated at the beginning, and the orange is generated afterwards to simulate events being uploaded to the stream. I'm not great at ERD models, so bear with me.
![ERD Model](https://github.com/user-attachments/assets/2d319d52-2326-4612-bf7b-34a6b01e1e28)


# Tech Stack & Components
- **AWS Kinesis**: Simulates a real-time log stream by ingesting event data.
- **AWS S3**: Stores raw event logs before processing.
- **Docker**: Runs a containerized consumer app that reads from Kinesis, aggregates data, and writes to S3.

## External Packages/Libraries
- `moto`: Used to mock the AWS systems so we don't actually use their real services.
- `boto3`: For S3 and Kinesis functions.
- `faker`: Used in the generation of all fake data used like names, emails, locations, metadata, etc.
- `pyscopg2`: Our interface/connection to the local PostgreSQL server.
- `pandas`: Used for managing table data as DataFrames and performing various modifications and aggregation.
- `matplotlib`: Used to visualize our data in graphs/plots.

### Logger
I'm a bit picky with my logger messages and formatting, so I created a `logger.py` helper class of sorts to help ease the logging process and output. It also uses the Singleton design to ensure only one file is made. I know this isn't standard, but it helped me with debugging and such. If I really sink my teeth into a project, I could spend days on just personalizing the logger.

# Generated Reports
## Report #1: Revenue Over Time
![report_revenue-over-time](https://github.com/user-attachments/assets/3a258a4e-ed81-4fc0-b94b-119f5534b9c2)
This is meant to theoretically project the revenue that the ad-hosting company is making off of auctions over time.

## Report #2: Company Statistics (Amazon)
![report_company-stats-Amazon](https://github.com/user-attachments/assets/b8e860b6-8f40-40ab-89fa-98c5b6584e02)
This is meant to visualize how much a specific company has spent on ad-space, the total events created from those ads, and how much they're spending-on-average per-event (over the course of a year).