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
    word = Column(String(5))
    first_letter = Column(String(1))
    second_letter = Column(String(1))
    third_letter = Column(String(1))
    fourth_letter = Column(String(1))
    fifth_letter = Column(String(1))


def create_words_from_dict_file(dict_file_path="/usr/share/dict/words"):
    with open(dict_file_path, "r") as f:
        words = f.read().splitlines()
    for word in words:
        if len(word) != 5 or any(c for c in word if c in punctuation):
            continue
        word = word.lower()
        yield Word(
            word=word,
            first_letter=word[0],
            second_letter=word[1],
            third_letter=word[2],
            fourth_letter=word[3],
            fifth_letter=word[4],
        )


def load_database_with_words(engine):
    with Session(engine) as session:
        words = create_words_from_dict_file()
        session.add_all(words)
        session.commit()


engine = create_engine(SQLITE_DB_URL, echo=False, future=True)
Base.metadata.create_all(engine)

if not SQLITE_DB_EXISTS:
    load_database_with_words(engine)


# TODO: Come up with a better name for this function
def filter_letters_not_used_in_correct_position(query, letter_column, letters):
    for letter in letters:
        query = query.filter(letter_column != letter)
    return query


def query_database_for_words(
    first_letter,
    second_letter,
    third_letter,
    fourth_letter,
    fifth_letter,
    not_first_letter,
    not_second_letter,
    not_third_letter,
    not_fourth_letter,
    not_fifth_letter,
    unused_letters,
):
    with Session(engine) as session:
        query = session.query(Word)

        if first_letter:
            query = query.filter(Word.first_letter == first_letter)
        elif not_first_letter:
            query = filter_letters_not_used_in_correct_position(
                query=query,
                letter_column=Word.first_letter,
                letters=not_first_letter,
            )

        if second_letter:
            query = query.filter(Word.second_letter == second_letter)
        elif not_second_letter:
            query = filter_letters_not_used_in_correct_position(
                query=query,
                letter_column=Word.second_letter,
                letters=not_second_letter,
            )

        if third_letter:
            query = query.filter(Word.third_letter == third_letter)
        elif not_third_letter:
            query = filter_letters_not_used_in_correct_position(
                query=query,
                letter_column=Word.third_letter,
                letters=not_third_letter,
            )

        if fourth_letter:
            query = query.filter(Word.fourth_letter == fourth_letter)
        elif not_fourth_letter:
            query = filter_letters_not_used_in_correct_position(
                query=query,
                letter_column=Word.fourth_letter,
                letters=not_fourth_letter,
            )

        if fifth_letter:
            query = query.filter(Word.fifth_letter == fifth_letter)
        elif not_fifth_letter:
            query = filter_letters_not_used_in_correct_position(
                query=query,
                letter_column=Word.fifth_letter,
                letters=not_fifth_letter,
            )

        included_letters = "".join(
            letters
            for letters in [
                not_first_letter,
                not_second_letter,
                not_third_letter,
                not_fourth_letter,
                not_fifth_letter,
            ]
            if letters
        )
        if included_letters:
            for included_letter in included_letters:
                query = query.filter(Word.word.contains(included_letter))

        if unused_letters:
            for unused_letter in unused_letters:
                query = query.filter(~Word.word.contains(unused_letter))

        for word in query:
            yield word.word


@click.command()
@click.option("--first_letter", "-1", type=str)
@click.option("--second_letter", "-2", type=str)
@click.option("--third_letter", "-3", type=str)
@click.option("--fourth_letter", "-4", type=str)
@click.option("--fifth_letter", "-5", type=str)
@click.option("--not_first_letter", "-n1", type=str)
@click.option("--not_second_letter", "-n2", type=str)
@click.option("--not_third_letter", "-n3", type=str)
@click.option("--not_fourth_letter", "-n4", type=str)
@click.option("--not_fifth_letter", "-n5", type=str)
@click.option("--unused_letters", "-u", type=str)
def cli(
    first_letter,
    second_letter,
    third_letter,
    fourth_letter,
    fifth_letter,
    not_first_letter,
    not_second_letter,
    not_third_letter,
    not_fourth_letter,
    not_fifth_letter,
    unused_letters,
):
    for word in query_database_for_words(
        first_letter=first_letter,
        second_letter=second_letter,
        third_letter=third_letter,
        fourth_letter=fourth_letter,
        fifth_letter=fifth_letter,
        not_first_letter=not_first_letter,
        not_second_letter=not_second_letter,
        not_third_letter=not_third_letter,
        not_fourth_letter=not_fourth_letter,
        not_fifth_letter=not_fifth_letter,
        unused_letters=unused_letters,
    ):
        click.echo(word)
