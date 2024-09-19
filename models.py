from database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, LargeBinary
from sqlalchemy.orm import relationship

# The Users class is created to represent the 'users' table in the database.
# The Base variable establishes the connection between the class and the database.
class Users(Base):
    __tablename__ = 'users'  # Specifies the table name

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Primary key, auto-incremented
    tc = Column(Integer)  # National ID number
    ad = Column(String)  # First name
    soyad = Column(String)  # Last name
    email = Column(String, unique=True)  # Unique email address
    telno = Column(String)  # Phone number
    username = Column(String, unique=True)  # Unique username
    hashed_password = Column(String)  # Encrypted password
    role = Column(String, default='user')  # Role of the user, default is 'user'
    owner = Column(Boolean, default=False)  # Boolean flag indicating if the user is an owner
    uzman = Column(Boolean, default=False)  # Boolean flag indicating if the user is an expert
    sekreter = Column(Boolean, default=False)  # Boolean flag indicating if the user is a secretary
    is_active = Column(Boolean, default=False)  # Boolean flag indicating if the user is active
    is_delete = Column(Boolean, default=False)  # Boolean flag indicating if the user is deleted

    # Relationships with the Todos table, linking expert and secretary users to tasks
    users_todos_uzman = relationship("Todos", foreign_keys='Todos.uzman_id', back_populates="todos_users_uzman")
    users_todos_sekreter = relationship("Todos", foreign_keys='Todos.sekreter_id', back_populates="todos_users_sekreter")


# The Todos class represents the 'todos' table, containing task-related information.
class Todos(Base):
    __tablename__ = "todos"  # Specifies the table name

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Primary key, auto-incremented
    start_time = Column(DateTime)  # Task start time
    end_time = Column(DateTime)  # Task end time
    uzman_id = Column(Integer, ForeignKey("users.id"))  # Foreign key linking to the expert user
    sekreter_id = Column(Integer, ForeignKey("users.id"))  # Foreign key linking to the secretary user
    musteri_id = Column(Integer, ForeignKey("customers.id"))  # Foreign key linking to the customer
    charge_id = Column(Integer, ForeignKey("charge.id"))  # Foreign key linking to the charge
    status_id = Column(Integer, ForeignKey("status.id"))  # Foreign key linking to the status
    is_delete = Column(Boolean, default=False)  # Boolean flag indicating if the task is deleted
    description = Column(String)  # Task description

    # Relationships linking the task to an expert user, secretary, customer, charge, and status
    todos_users_uzman = relationship("Users", uselist=False, foreign_keys=[uzman_id], back_populates="users_todos_uzman")
    todos_users_sekreter = relationship("Users", uselist=False, foreign_keys=[sekreter_id], back_populates="users_todos_sekreter")
    todos_customers = relationship("Customers", uselist=False, foreign_keys=[musteri_id], back_populates="customers_todos")
    todos_charge = relationship("Charge", uselist=False, foreign_keys=[charge_id], back_populates="charge_todos")
    todos_status = relationship("Status", uselist=False, foreign_keys=[status_id], back_populates="status_todos")


# The Charge class represents the 'charge' table, containing pricing-related information.
class Charge(Base):
    __tablename__ = 'charge'  # Specifies the table name

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Primary key, auto-incremented
    net = Column(Numeric(precision=10, scale=2))  # Net charge
    tax = Column(Numeric(precision=10, scale=2))  # Tax amount
    total = Column(Numeric(precision=10, scale=2))  # Total charge
    charge_name = Column(String)  # Charge name or description
    is_active = Column(Boolean, default=True)  # Boolean flag indicating if the charge is active
    is_delete = Column(Boolean, default=False)  # Boolean flag indicating if the charge is deleted

    # Relationship linking the charge to tasks (Todos)
    charge_todos = relationship("Todos", foreign_keys="Todos.charge_id", back_populates="todos_charge")


# The Customers class represents the 'customers' table, containing customer-related information.
class Customers(Base):
    __tablename__ = 'customers'  # Specifies the table name

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Primary key, auto-incremented
    tc = Column(Integer)  # National ID number
    ad = Column(String)  # First name
    soyad = Column(String)  # Last name
    email = Column(String, unique=True)  # Unique email address
    telno = Column(String)  # Phone number
    info = Column(String)  # Additional customer information
    address1 = Column(String)  # Address of the customer
    city = Column(String)  # City of the customer
    url = Column(String)  # Website or URL for the customer
    is_active = Column(Boolean, default=True)  # Boolean flag indicating if the customer is active
    is_delete = Column(Boolean, default=False)  # Boolean flag indicating if the customer is deleted

    # Relationships linking the customer to tasks and documents
    customers_todos = relationship("Todos", foreign_keys="Todos.musteri_id", back_populates="todos_customers")
    customers_documents = relationship("Documents", foreign_keys="Documents.customer_id", back_populates="documents_customers")


# The Documents class represents the 'documents' table, containing document-related information.
class Documents(Base):
    __tablename__ = "documents"  # Specifies the table name

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Primary key, auto-incremented
    file = Column(String)  # File name or path
    content = Column(String)  # Document content or description
    path = Column(String)  # Path to the file
    size = Column(Integer)  # Size of the file
    customer_id = Column(Integer, ForeignKey("customers.id"))  # Foreign key linking to the customer

    # Relationship linking the document to the customer
    documents_customers = relationship("Customers", uselist=False, foreign_keys=[customer_id], back_populates="customers_documents")


# The Status class represents the 'status' table, containing status-related information.
class Status(Base):
    __tablename__ = "status"  # Specifies the table name

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Primary key, auto-incremented
    status_name = Column(String)  # Name of the status
    is_active = Column(Boolean, default=True)  # Boolean flag indicating if the status is active
    is_delete = Column(Boolean, default=False)  # Boolean flag indicating if the status is deleted

    # Relationship linking the status to tasks (Todos)
    status_todos = relationship("Todos", foreign_keys="Todos.status_id", back_populates="todos_status")
