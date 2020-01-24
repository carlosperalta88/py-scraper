def format_data(data, categories):
    return {key: value for key, value in zip(categories, data)}


class Formatter:
    def __init__(self):
        self.default_format = {
            "cause_history": [
                {
                    "book": "book",
                    "history": ["folio", "doc", "attachment", "stage", "procedure",
                                "procedure_description", "procedure_date", "document_page"]
                },
            ],
            "exhort": ["role_origin", "exhort_type", "role_destination", "exhort_order_date",
                       "exhort_added_date", "court_destined", "exhort_status"],
            "role_destination_detail": ["doc", "date", "reference", "procedure"],
            "pending_docs": [
                {
                    "book": "book",
                    "docs": ["doc", "attachment", "date_added", "doc_type", "requester"]
                }
            ],
            "receptor": ["book", "retrieve_data", "status"],
            "role_search": ["role", "date", "cover", "court"],
            "status": ""
            }

    def get_history(self, history):
        book = history[self.default_format["cause_history"][0]["book"]]
        history_detail = list(map(lambda x: format_data(x, self.default_format["cause_history"][0]["history"]),
                              history["history"]))
        return {"book": book, "history": history_detail}

    def get_docs(self, pdocs):
        book = pdocs[self.default_format["pending_docs"][0]["book"]]
        docs_details = list(map(lambda x: format_data(x, self.default_format["pending_docs"][0]["docs"]), pdocs["docs"]))
        return {"book": book, "docs": docs_details}

    def get_exhort_details(self, exhort, exhort_detail):
        ex_details = list(filter(lambda x: x[0] == exhort["role_destination"], exhort_detail))
        ex_details_formatted = list(map(lambda y: format_data(y, self.default_format["role_destination_detail"]),
                                    ex_details[0][1]))  # TODO: revisit this
        exhort["role_destination_detail"] = ex_details_formatted
        return exhort

    def formatter(self, raw_data):
        cause_history = list(map(lambda x: self.get_history(x), raw_data["cause_history"]))
        exhorts = list(map(lambda x: format_data(x, self.default_format["exhort"]), raw_data["exhort"]))
        exhorts_with_rdd = list(map(lambda x: self.get_exhort_details(x, raw_data["exhorts"]), exhorts))
        pending_docs = list(map(lambda x: self.get_docs(x), raw_data["pending_docs"]))
        receptor = list(map(lambda x: format_data(x, self.default_format["receptor"]), raw_data["receptor"]))
        role_search = list(map(lambda x: format_data(x, self.default_format["role_search"]), raw_data["role_search"]))
        status = raw_data["status"].split(": ")[1] if len(raw_data["status"]) > 0 else ""

        return {"cause_history": cause_history, "exhorts": exhorts_with_rdd, "pending_docs": pending_docs,
                "receptor": receptor, "role_search": role_search, "status": status}
