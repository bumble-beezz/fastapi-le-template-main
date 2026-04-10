import typer
from app.database import create_db_and_tables, get_cli_session, drop_all
from app.models import *
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from app.utilities import encrypt_password
import csv

cli = typer.Typer()

@cli.command()
def initialize():
    with get_cli_session() as db:
        drop_all()
        create_db_and_tables()
        
        bob = UserBase(username='bob', email='bob@mail.com', password=encrypt_password("bobpass"))
        bob_db = User.model_validate(bob)
        db.add(bob_db)
        db.commit()

        with open("students.csv", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                student = Student(
                    first_name=row["FirstName"],
                    last_name=row["LastName"],
                    programme=row["Programme"],
                    year_started=int(row["YearStarted"]),
                    picture=row["Picture"]
                )
                db.add(student)
        db.commit()
        
        print("Database Initialized")

@cli.command()
def test():
    print("You're already in the test")

if __name__ == "__main__":
    cli()