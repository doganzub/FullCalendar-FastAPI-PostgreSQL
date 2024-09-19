class CreateTables():
    im = None  # Database cursor
    vt = None  # Database connection

    @classmethod
    def create_tables(cls):
        import psycopg2
        # Connect to the PostgreSQL database using psycopg2
        with psycopg2.connect(host="localhost", database="Your_DataBase", user="postgres", password="your_password",
                              port="5432") as cls.vt:
            # Create a cursor for executing SQL commands
            cls.im = cls.vt.cursor()
            print("Connected to the database for the 'users' table and created a cursor")

            # Execute SQL commands to create the necessary tables if they do not exist
            cls.im.execute("""   
                CREATE TABLE IF NOT EXISTS public.users
                (
                    id serial NOT NULL,  -- Auto-incrementing ID for users
                    tc integer,  -- National ID number
                    ad varchar,  -- First name
                    soyad varchar,  -- Last name
                    email varchar,  -- Email address, unique
                    telno varchar,  -- Phone number
                    username varchar,  -- Username, unique
                    hashed_password varchar,  -- Password (hashed)
                    role varchar,  -- User role (e.g., admin, user)
                    owner boolean,  -- Flag indicating if the user is an owner
                    uzman boolean,  -- Flag indicating if the user is an expert
                    sekreter boolean,  -- Flag indicating if the user is a secretary
                    is_active boolean,  -- Flag indicating if the user is active
                    is_delete boolean,  -- Flag indicating if the user is marked as deleted
                    CONSTRAINT users_pkey PRIMARY KEY (id),  -- Primary key constraint
                    CONSTRAINT users_email_key UNIQUE (email),  -- Unique constraint for email
                    CONSTRAINT users_username_key UNIQUE (username)  -- Unique constraint for username
                );                      

                CREATE TABLE IF NOT EXISTS public.customers
                (
                    id serial NOT NULL,  -- Auto-incrementing ID for customers
                    tc integer,  -- National ID number
                    ad varchar,  -- First name
                    soyad varchar,  -- Last name
                    email varchar,  -- Email address, unique
                    telno varchar,  -- Phone number
                    info varchar,  -- Additional customer information
                    address1 varchar,  -- Address
                    city varchar,  -- City
                    postalcode varchar,  -- Postal code
                    is_active boolean,  -- Flag indicating if the customer is active
                    is_delete boolean,  -- Flag indicating if the customer is marked as deleted
                    CONSTRAINT customers_pkey PRIMARY KEY (id),  -- Primary key constraint
                    CONSTRAINT customers_email_key UNIQUE (email)  -- Unique constraint for email
                );

                CREATE TABLE IF NOT EXISTS public.charge
                (
                    id serial NOT NULL,  -- Auto-incrementing ID for charges
                    net Numeric,  -- Net charge amount
                    tax Numeric,  -- Tax amount
                    total Numeric,  -- Total charge amount
                    charge_name varchar,  -- Charge description
                    is_active boolean,  -- Flag indicating if the charge is active
                    is_delete boolean,  -- Flag indicating if the charge is marked as deleted
                    CONSTRAINT charge_pkey PRIMARY KEY (id)  -- Primary key constraint
                );
                
                CREATE TABLE IF NOT EXISTS public.status
                (
                    id serial NOT NULL,  -- Auto-incrementing ID for status entries
                    status_name varchar,  -- Status description
                    is_active boolean,  -- Flag indicating if the status is active
                    is_delete boolean,  -- Flag indicating if the status is marked as deleted
                    CONSTRAINT status_pkey PRIMARY KEY (id)  -- Primary key constraint
                ); 
                            
              CREATE TABLE IF NOT EXISTS public.todos
                (
                    id serial NOT NULL,  -- Auto-incrementing ID for tasks
                    start_time DateTime,  -- Task start time
                    end_time DateTime,  -- Task end time
                    create_date date,  -- Task creation date
                    uzman_id integer,  -- Foreign key to the expert user
                    sekreter_id integer,  -- Foreign key to the secretary user
                    musteri_id integer,  -- Foreign key to the customer
                    charge_id integer,  -- Foreign key to the charge
                    status_id integer,  -- Foreign key to the status
                    is_delete boolean,  -- Flag indicating if the task is marked as deleted
                    description varchar,  -- Task description
                    CONSTRAINT todos_pkey PRIMARY KEY (id),  -- Primary key constraint

                    -- Foreign key constraints linking to other tables
                    CONSTRAINT todos_uzman_id_fkey FOREIGN KEY (uzman_id)
                        REFERENCES public.users (id) MATCH SIMPLE
                        ON UPDATE NO ACTION
                        ON DELETE NO ACTION,
        
                    CONSTRAINT todos_sekreter_id_fkey FOREIGN KEY (sekreter_id)
                        REFERENCES public.users (id) MATCH SIMPLE
                        ON UPDATE NO ACTION
                        ON DELETE NO ACTION,   
        
                    CONSTRAINT todos_musteri_id_fkey FOREIGN KEY (musteri_id)
                        REFERENCES public.customers (id) MATCH SIMPLE
                        ON UPDATE NO ACTION
                        ON DELETE NO ACTION,
        
                    CONSTRAINT todos_charge_id_fkey FOREIGN KEY (charge_id)
                        REFERENCES public.charge (id) MATCH SIMPLE
                        ON UPDATE NO ACTION
                        ON DELETE NO ACTION,
                        
                    CONSTRAINT todos_status_id_fkey FOREIGN KEY (status_id)
                        REFERENCES public.status (id) MATCH SIMPLE
                        ON UPDATE NO ACTION
                        ON DELETE NO ACTION                             
                );
                """)

            # Commit the transaction to save the changes to the database
            cls.vt.commit()
            print("The 'users' table was created or connected successfully")


# Call the method to create the tables
CreateTables.create_tables()
