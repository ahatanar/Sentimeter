from src.database import get_table

class UserModel:
    TABLE_NAME = "users"

    @classmethod
    def save(cls, google_id, email, name):
        table = get_table(cls.TABLE_NAME)
        table.put_item(
            Item={
                "user_id": google_id,
                "email": email,
                "name": name
            }
        )

    @classmethod
    def find_by_google_id(cls, google_id):
        table = get_table(cls.TABLE_NAME)
        response = table.get_item(Key={"user_id": google_id})
        return response.get("Item")  #