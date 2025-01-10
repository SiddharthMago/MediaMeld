import os
from dotenv import load_dotenv

import psycopg2
from psycopg2 import sql

load_dotenv()

def convert_user_tuple_to_dict(user_tuple):
    return {
        "user_id": user_tuple[0],
        "user_name": user_tuple[1],
        "user_email": user_tuple[2],
        "user_password": user_tuple[3]
    }


# Establishing connection to the database
def get_database_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


# Insert user details into the database
def insert_into_user_details(user_name, user_email, user_password):
    conn = get_database_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("INSERT INTO public.user_details (user_name, user_email, user_password) VALUES (%s, %s, %s)"),
                (user_name, user_email, user_password)
            )
            conn.commit()
    finally:
        conn.close()


# Retrieve user details from the database
def get_from_user_details(user_email):
    conn = get_database_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("SELECT * FROM public.user_details WHERE user_email = %s"),
                (user_email,)
            )
            user_details = cursor.fetchone()
            if user_details:
                return convert_user_tuple_to_dict(user_details)
            else:
                return None
    finally:
        conn.close()


def get_unique_user_ids():
    conn = get_database_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("SELECT DISTINCT(user_id), user_name, user_email FROM public.user_details")
            )
            unique_ids = cursor.fetchall()
            return unique_ids
    finally:
        conn.close()


# Converts Image_Metadata to Image_type
def metadata_to_type(image_metadata):
    image_type = image_metadata.split('.')
    return image_type[1]


# Store image bytes into the database
def store_image_bytes(image_bytes, user_id, image_metadata, image_type):
    conn = get_database_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("INSERT INTO public.images (user_id, image, image_metadata, image_type) VALUES (%s, %s::BYTES, %s, %s)"),
                (user_id, image_bytes, image_metadata, image_type)
            )
            conn.commit()
    finally:
        conn.close()


# Retrieve images from the database given email
def get_images(user_email):
    conn = get_database_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("SELECT image FROM public.images WHERE public.images.user_id IN (SELECT public.user_details.user_id FROM public.user_details WHERE public.user_details.user_email = %s)"),
                (user_email,)
            )
            images = cursor.fetchall()
            return images
    finally:
        conn.close()


def delete_image_from_images(image_id):
    conn = get_database_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("DELETE FROM images WHERE image_id = %s"),(image_id,)
            )
    finally:
        conn.close()


def store_audio_bytes(audio_bytes, audio_metadata):
    conn = get_database_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("INSERT INTO public.audio (audio, audio_metadata) VALUES (%s::BYTES, %s)"),
                (audio_bytes, audio_metadata)
            )
            conn.commit()
    finally:
        conn.close()


def get_audio_ids():
    conn = get_database_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("SELECT audio_id, audio FROM public.audio")
            )
            audio_ids = cursor.fetchall()
            return audio_ids
    finally:
        conn.close()


def get_audio(audio_id):
    conn = get_database_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("SELECT audio FROM public.audio WHERE public.audio.audio_id = %s"),
                (audio_id,)
            )
            audio = cursor.fetchall()
            return audio[0][0]
    finally:
        conn.close()