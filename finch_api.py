import requests
from finch import Finch
import os


class FinchSetUp():

    def __init__(self):
        self.products = ["directory", "individual", "employment", "company"]
        self.code = None
        self.access_token = None
        self.client_id = os.environ['client_id']
        self.client_secret = os.environ['client_secret']
        self.customer_id = os.environ['customer_id']
        self.customer_name = os.environ['customer_name']

    
    def check_session(self):
        print("check_session")
        if not self.access_token:
            return self.get_session()
        
        return False

    
    def set_code(self, code):
        print("set_code")
        self.code = code
    
    def set_access_token(self, token):
        print("set_access_token")
        self.access_token = token


    def get_session(self):
        print("get_session")
        try:
            response = requests.post(
                "https://api.tryfinch.com/connect/sessions",
                auth=(self.client_id, self.client_secret),
                json={
                    "customer_id": self.customer_id,
                    "customer_name": self.customer_name,
                    "products": self.products,
                    "redirect_uri": "http://127.0.0.1:5000/set_code",
                    "sandbox": "finch",
                },
            )
            
            res = response.json()
            
            if response.status_code == 400 and res.get("finch_code") == "connection_already_exists":
                connection_id = res.get("context").get("connection_id")

                res = self.get_re_session(connection_id)
            elif response.status_code > 200:
                raise Exception(res.get("error"))

                
            print(res)
            connect_url = res.get("connect_url")
            print(connect_url)
            return connect_url
        except Exception as e:
            raise e


    def get_re_session(self, connection_id):
        print("get_re_session")
        response = requests.post(
            "https://api.tryfinch.com/connect/sessions/reauthenticate",
            auth=(self.client_id, self.client_secret),
            json={
                "connection_id": connection_id,
                "minutes_to_expire": 10,
                "products":self.products,
                "redirect_uri": "http://127.0.0.1:5000/set_code",
                "sandbox": "finch",
            },
        )

        return response.json()

    def get_auth(self):
        print("get_auth")
        
        client = Finch(
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        create_access_token_response = client.access_tokens.create(
            code=self.code,
        )

        access_token = create_access_token_response.model_dump().get("access_token")

        return access_token


    def get_company(self):
        print("get_company")
        try:
            client = Finch(
                access_token=self.access_token,
            )
            company = client.hris.company.retrieve()
            return company.model_dump()
        except Exception as e:
            raise e
    

    def get_directory(self):
        print("get_directory")
        try:
            client = Finch(
                access_token=self.access_token,
            )
            page = client.hris.directory.list()
            return page.model_dump()
        except Exception as e:
            raise e
    
    def get_formatted_directory(self):
        print("get_formatted_directory")
        try:
            client = Finch(
                access_token=self.access_token,
            )
            page = client.hris.directory.list()
            return self.format_directory(page.model_dump())
        except Exception as e:
            raise e


    def get_individual(self, id):
        print("get_Individual")
        try:
            client = Finch(
                access_token=self.access_token,
            )
            individual = client.hris.individuals.retrieve_many(
                requests=[{
                    "individual_id": id
                }], 
            )
        except Exception as e:
            raise e

        return individual.model_dump()
    
    def get_employment(self, id):
        print("get_employment")
        try:
            client = Finch(
                access_token=self.access_token,
            )
            employment = client.hris.employments.retrieve_many(
                requests=[{
                    "individual_id": id
                }],
            )

            return employment.model_dump()
        except Exception as e:
            raise e


    def format_directory(self, directory):
        individuals = directory.get("individuals", [])

        id_to_name = {}
        for person in individuals:
            full_name = " ".join(filter(None, [
                person.get("first_name"),
                person.get("middle_name"),
                person.get("last_name")
            ]))
            id_to_name[person["id"]] = full_name

        clean_map = {"True": {}, "False": {}}

        for person in individuals:
            is_active_key = str(person.get("is_active", False))
            department = person.get("department", {}).get("name", "Unknown")
            full_name = id_to_name[person["id"]]

            manager_id = person.get("manager", {}).get("id") if person.get("manager") else None
            manager_name = id_to_name.get(manager_id, "No Manager")

            entry = {"Name": full_name, "id":  person["id"] }

            # Initialize department
            if department not in clean_map[is_active_key]:
                clean_map[is_active_key][department] = {}

            # Initialize manager group
            if manager_name not in clean_map[is_active_key][department]:
                clean_map[is_active_key][department][manager_name] = []

            clean_map[is_active_key][department][manager_name].append(entry)

        return clean_map
