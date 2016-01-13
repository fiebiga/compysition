from __future__ import absolute_import

from compysition.actor import Actor
import json
from lxml import etree
from .util.dataformat import str_to_json
from xml.sax.saxutils import XMLGenerator
import xmltodict


class UnescapedDictXMLGenerator(XMLGenerator):
    """
    Simple class designed to enable the use of an unescaped functionality
    in the event that dictionary value data is already XML
    """

    def characters(self, content):
        try:
            etree.fromstring(content)
            self._write(content)
        except:
            XMLGenerator.characters(self, content)

class DictToXML(Actor):
    """
    *Actor implementation of the dicttoxml lib. Converts an incoming dictionary to XML*
    Input(s)/Output Types:
        - Input: <(str) dict>
        - Input: <(str) json>
            | Refers to strict JSON standards, though this is implemented in python as a 'dict'
        - Input: <dict>
        - Input: <json>
            | Refers to strict JSON standards, though this is implemented in python as a 'dict'
        - Output: <(str) XML>

    Parameters:
        - name (REQ) (str)
            | Actor Name

        - escape_xml (bool) (Default: False)
            | If set to True, a dict key or nested dict key that contains an XML-style string element will be
            | XML escaped. If False, that XML will be retained in the XML element node created from the dictionary key
            | as a literal XML tree
    """

    def __init__(self, name, escape_xml=False, key=None, *args, **kwargs):
        # Override the dicttoxml xml_escape method with a simple echo
        if escape_xml:
            setattr(xmltodict, "XMLGenerator", UnescapedDictXMLGenerator)

        super(DictToXML, self).__init__(name, *args, **kwargs)
        self.input_types_processing_map.update({
            dict: self._process_dict_input
        })

        # TODO: Remove this once "all" is no longer universal to all Actors
        self.input_types_processing_map.pop("all", None)
        self.key = key or name

    def _process_dict_input(self, data):
        # Documents must have only 1 root
        if len(data) > 1:
            data = {self.key: data}

        return data

    def _process_str_input(self, data):
        data = str_to_json(data)
        return self._process_dict_input(data)

    def consume(self, event, *args, **kwargs):
        try:
            xml = self.convert(event.data)
            if xml is not None:
                event.data = str(xml)
            else:
                raise Exception("Incoming data was not a dictionary")

            self.send_event(event)
        except Exception as err:
            self.logger.error("Unable to convert XML: {0}".format(err), event=event)
            self.send_error(event)

    def convert(self, data):
        return xmltodict.unparse(data)

    @staticmethod
    def find_dict_paths(dict_, path=None):
        """
        This is currently unused. This was the original direction for enabling unescaped dict to xml transformations
        for dictionaries that contained values that were ALREADY xml, but I decided to go with the parser replacement
        for now instead. I kept this code in here because it's not a bad function to find dict paths, and I may
        switch to this method in the future after performance analysis
        """
        def concat_path(path, key):
            if path is None:
                return (key, )
            else:
                return tuple(list(path) + [key])

        for key, value in dict_.iteritems():
            if isinstance(value, dict):
                for result in DictToXML.find_dict_paths(value, concat_path(path, key)):
                    yield result
            else:
                try:
                    data = etree.fromstring(value)
                except:
                    data = None

                if data is not None:
                    yield (concat_path(path, key), data)

    def populate_dict_paths(self):
        pass

def main():
    """"request_data": "<dt_application xmlns=\"x-schema:http://www.qa.dealertrack.com/schemas/dtapp_v2_0.xdr\" active=\"yes\" status=\"new\" dtversion=\"2.0\"> \t<key_data optout=\"no\"> \t\t<dt_lender_id>TST</dt_lender_id> \t\t<dt_dealer_id>154769</dt_dealer_id> \t\t<dt_app_id>16A8356605</dt_app_id> \t\t<lender_dealer_id>1234</lender_dealer_id> \t\t<lender_app_id/> \t\t<requestdate>2014-10-15T09:29:46</requestdate> \t\t<credit_type type=\"joint\"/> \t\t<app_type type=\"personal\"/> \t\t<product_type type=\"retail\" paymentcall=\"no\"/> \t\t<vehicle_type type=\"new\" trade=\"no\"/> \t\t<cust_credit_type type=\"none\"/> \t\t<loan_type type=\"auto\"/> \t\t<source/> \t\t<user_name>CU Answers Integrations</user_name> \t</key_data> \t<application_data type=\"newapplication\" regb=\"yes\" comu_state=\"no\" swap=\"no\" cosigner_intent=\"na\" program_routing_ind=\"none\"> \t\t<applicant_data type=\"primary\"> \t\t\t<first_name>ADAM</first_name> \t\t\t<mi/> \t\t\t<last_name>FIEBIG</last_name> \t\t\t<ssn>355555555</ssn> \t\t\t<dob>1985-12-23</dob> \t\t\t<address type=\"current\"> \t\t\t\t<street_no>123</street_no> \t\t\t\t<street_name>EASY RD</street_name> \t\t\t\t<street_type>AV</street_type> \t\t\t\t<street_type_desc>AVENUE</street_type_desc> \t\t\t\t<apt_no>11</apt_no> \t\t\t\t<city>GRANDVILLE</city> \t\t\t\t<state>MI</state> \t\t\t\t<zip_code>49418</zip_code> \t\t\t</address> \t\t\t<home_phone_no>6166633213</home_phone_no> \t\t\t<years_at_address>4</years_at_address> \t\t\t<months_at_address>3</months_at_address> \t\t\t<years_at_prv_address/> \t\t\t<months_at_prv_address/> \t\t\t<email_address/> \t\t\t<housing_status type=\"rent\"/> \t\t\t<mortgage_rent>544</mortgage_rent> \t\t\t<employment_data type=\"current\"> \t\t\t\t<emp_status type=\"employed\"/> \t\t\t\t<employed_by>YOUR MOM</employed_by> \t\t\t\t<work_phone_no>6164433215</work_phone_no> \t\t\t\t<years_employed>10</years_employed> \t\t\t\t<months_employed>3</months_employed> \t\t\t\t<occupation>PROGRAMMING GOD</occupation> \t\t\t\t<salary type=\"monthly\">5000</salary> \t\t\t</employment_data> \t\t\t<other_income>2300</other_income> \t\t\t<source_other_income>RUNNING THE STREETS</source_other_income> \t\t\t<comments>I Would Like To Have A Car For Nothing. That Is My Preference. Thank You</comments> \t\t\t<driver_license_no/> \t\t\t<driver_license_state/> \t\t\t<other_phone_no>6166344192</other_phone_no> \t\t</applicant_data> \t\t<applicant_data type=\"coapplicant\"> \t\t\t<first_name>HILARY</first_name> \t\t\t<mi/> \t\t\t<last_name>FIEBIG</last_name> \t\t\t<ssn>355555556</ssn> \t\t\t<dob>1987-12-12</dob> \t\t\t<address type=\"current\"> \t\t\t\t<street_no>123</street_no> \t\t\t\t<street_name>EASY RD</street_name> \t\t\t\t<street_type>AV</street_type> \t\t\t\t<street_type_desc>AVENUE</street_type_desc> \t\t\t\t<apt_no>11</apt_no> \t\t\t\t<city>GRANDVILLE</city> \t\t\t\t<state>MI</state> \t\t\t\t<zip_code>49418</zip_code> \t\t\t</address> \t\t\t<home_phone_no>6162233214</home_phone_no> \t\t\t<years_at_address>4</years_at_address> \t\t\t<months_at_address>3</months_at_address> \t\t\t<years_at_prv_address/> \t\t\t<months_at_prv_address/> \t\t\t<email_address/> \t\t\t<housing_status type=\"rent\"/> \t\t\t<mortgage_rent>300</mortgage_rent> \t\t\t<employment_data type=\"current\"> \t\t\t\t<emp_status type=\"employed\"/> \t\t\t\t<employed_by>THE SCHOOL OF HARD KNOCKS</employed_by> \t\t\t\t<work_phone_no>6162344321</work_phone_no> \t\t\t\t<years_employed>10</years_employed> \t\t\t\t<months_employed>4</months_employed> \t\t\t\t<occupation>PIMP DADDY</occupation> \t\t\t\t<salary type=\"weekly\">4000</salary> \t\t\t</employment_data> \t\t\t<other_income>4000</other_income> \t\t\t<source_other_income>RUNNING THE STREETS</source_other_income> \t\t\t<relationship type=\"spouse\"/> \t\t\t<driver_license_no/> \t\t\t<driver_license_state/> \t\t\t<other_phone_no/> \t\t</applicant_data> \t\t<vehicle_data> \t\t\t<certified_used/> \t\t\t<book_year>2014</book_year> \t\t\t<book_make>HONDA</book_make> \t\t\t<model>ACCORD SEDAN</model> \t\t\t<trim>4DR EX-L V6 AT W/NAV</trim> \t\t\t<chrome_style_id>363819</chrome_style_id> \t\t\t<chrome_year>2014</chrome_year> \t\t\t<chrome_make>HONDA</chrome_make> \t\t\t<chrome_model>ACCORD SEDAN</chrome_model> \t\t\t<chrome_trim>4DR V6 AUTO EX-L W/NAVI PZEV</chrome_trim> \t\t\t<veh_desc_source/> \t\t\t<bookout>N</bookout> \t\t\t<bookout_options/> \t\t\t<uvc/> \t\t\t<vin_uvc/> \t\t\t<trade_financed/> \t\t\t<trade_monthly_payment/> \t\t\t<lbo_bookout> \t\t\t\t\t<lbo_book source=\"black\"> \t\t\t\t\t\t\t<lbo_book_value>9321</lbo_book_value> \t\t\t\t\t</lbo_book> \t\t\t</lbo_bookout> \t\t</vehicle_data> \t\t<product_data> \t\t\t<term_months>72</term_months> \t\t\t<cash_selling_price>32000</cash_selling_price> \t\t\t<ttl_estimate>4000</ttl_estimate> \t\t\t<cash_down>10000</cash_down> \t\t\t<rebate>1000</rebate> \t\t\t<unpaid_balance>30000</unpaid_balance> \t\t\t<creditlife/> \t\t\t<acc_health_insurance/> \t\t\t<est_amt_financed>30000</est_amt_financed> \t\t\t<invoice_amount>20000</invoice_amount> \t\t\t<new_car_mileage>233</new_car_mileage> \t\t\t<msrp>34000</msrp> \t\t\t<requested_apr>2.00</requested_apr> \t\t\t<lender_program/> \t\t\t<sales_tax>5000</sales_tax> \t\t\t<other_finance_fees/> \t\t\t<gap/> \t\t\t<other_fees/> \t\t\t<wholesale_value condition=\"na\" type=\"na\">0</wholesale_value> \t\t\t<wholesale_source/> \t\t\t<retail_value condition=\"na\">0</retail_value> \t\t\t<retail_source/> \t\t\t<app_opt_program id=\"\"/> \t\t</product_data> \t</application_data> </dt_application>",
    """
    test = """{
    "comment": "This is not a test, \\"don",
    "request_data": "<dt_application xmlns=\\"",
    "meta_id": "35808e56eb6247e3aa3f62e6b70a7084",
    "partner": "dealertrack",
    "target_id": "TST",
    "sender_id": "142030"
    }"""

    print json.dumps(test)

    test = json.loads(test)
    print test
    print json.dumps(test)
    act = DictToXML("name", escape_xml=True)
    #test = act._process_str_input(test)
    #print act.convert(test)


if __name__ == "__main__":
    main()