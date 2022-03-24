import os
from string import punctuation

import click
from sqlalchemy import Column, String, and_, create_engine
from sqlalchemy.orm import Session, declarative_base

WORD_DB_PATH = os.path.abspath(
    os.path.expanduser("~/.cache/wordle_helper/words.sqlite")
)
_current_file_parent_dir = os.path.dirname(os.path.abspath(__file__))
WORD_SOURCE_PATH = os.path.join(_current_file_parent_dir, "data/sgb-words.txt")

Base = declarative_base()


class Word(Base):
    __tablename__ = "words"
    word = Column(String(5), primary_key=True)
    first_letter = Column(String(1))
    second_letter = Column(String(1))
    third_letter = Column(String(1))
    fourth_letter = Column(String(1))
    fifth_letter = Column(String(1))


def create_words_from_file(word_source_path=WORD_SOURCE_PATH):
    with open(word_source_path, "r") as f:
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


def load_database_with_words(engine, word_source_path=WORD_SOURCE_PATH):
    with Session(engine) as session:
        words = create_words_from_file(word_source_path=word_source_path)
        session.add_all(words)
        session.commit()


def setup_database(word_db_path=WORD_DB_PATH):
    word_db_parent_dir = os.path.dirname(word_db_path)
    if not os.path.exists(word_db_parent_dir):
        os.makedirs(word_db_parent_dir)

    db_already_exists = os.path.exists(word_db_path)
    word_db_url = f"sqlite:///{word_db_path}"
    engine = create_engine(word_db_url, echo=False, future=True)
    Base.metadata.create_all(engine)

    if not db_already_exists:
        load_database_with_words(engine)

    return engine


def query_database_for_words(
    engine,
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

        columns_letter_and_not_letters = [
            (Word.first_letter, first_letter, not_first_letter),
            (Word.second_letter, second_letter, not_second_letter),
            (Word.third_letter, third_letter, not_third_letter),
            (Word.fourth_letter, fourth_letter, not_fourth_letter),
            (Word.fifth_letter, fifth_letter, not_fifth_letter),
        ]
        for letter_column, letter, not_letters in columns_letter_and_not_letters:
            if letter:
                query = query.filter(letter_column == letter)
            elif not_letters:
                query = query.filter(and_(letter_column != l for l in not_letters))

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
            query = query.filter(and_(Word.word.contains(l) for l in included_letters))

        if unused_letters:
            query = query.filter(and_(~Word.word.contains(ul) for ul in unused_letters))

        for word in query.distinct():
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
    engine = setup_database()
    for word in query_database_for_words(
        engine=engine,
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
