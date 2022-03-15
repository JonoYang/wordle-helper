import os
from string import punctuation

import click
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base

SQLITE_DB_FILE_PATH = os.path.abspath(os.path.expanduser("~/words.sqlite"))
SQLITE_DB_URL = f"sqlite:///{SQLITE_DB_FILE_PATH}"
SQLITE_DB_EXISTS = os.path.exists(SQLITE_DB_FILE_PATH)


Base = declarative_base()


class Word(Base):
    __tablename__ = "words"
    id = Column(Integer, primary_key=True)
    first_letter = Column(String(1))
    second_letter = Column(String(1))
    third_letter = Column(String(1))
    fourth_letter = Column(String(1))
    fifth_letter = Column(String(1))

    def word(self):
        return f"{self.first_letter}{self.second_letter}{self.third_letter}{self.fourth_letter}{self.fifth_letter}"


def create_words_from_dict_file(dict_file_path="/usr/share/dict/words"):
    with open(dict_file_path, "r") as f:
        words = f.read().splitlines()
    for word in words:
        if len(word) != 5 or any(c for c in word if c in punctuation):
            continue
        word = word.lower()
        yield Word(
            first_letter=word[0],
            second_letter=word[1],
            third_letter=word[2],
            fourth_letter=word[3],
            fifth_letter=word[4],
        )


def load_database(engine):
    with Session(engine) as session:
        words = create_words_from_dict_file()
        session.add_all(words)
        session.commit()


engine = create_engine(SQLITE_DB_URL, echo=False, future=True)
Base.metadata.create_all(engine)

if not SQLITE_DB_EXISTS:
    load_database(engine)


@click.command()
@click.option("--first_letter", "-1", type=str)
@click.option("--second_letter", "-2", type=str)
@click.option("--third_letter", "-3", type=str)
@click.option("--fourth_letter", "-4", type=str)
@click.option("--fifth_letter", "-5", type=str)
@click.option("--unused_letters", "-u", type=str)
def cli(
    first_letter,
    second_letter,
    third_letter,
    fourth_letter,
    fifth_letter,
    unused_letters,
):
    with Session(engine) as session:
        query = session.query(Word)

        if first_letter:
            query = query.filter(Word.first_letter == first_letter)
        if second_letter:
            query = query.filter(Word.second_letter == second_letter)
        if third_letter:
            query = query.filter(Word.third_letter == third_letter)
        if fourth_letter:
            query = query.filter(Word.fourth_letter == fourth_letter)
        if fifth_letter:
            query = query.filter(Word.fifth_letter == fifth_letter)
        if unused_letters:
            for unused_letter in unused_letters:
                query = (
                    query.filter(Word.first_letter != unused_letter)
                    .filter(Word.second_letter != unused_letter)
                    .filter(Word.third_letter != unused_letter)
                    .filter(Word.fourth_letter != unused_letter)
                    .filter(Word.fifth_letter != unused_letter)
                )

        for word in query:
            print(word.word())
