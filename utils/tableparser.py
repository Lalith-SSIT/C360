
import pandas as pd
import json

def accounts_with_opportunities(excel_path):
    sales_dictionary = {}
    accounts_df = pd.read_excel(excel_path, sheet_name="Account")
    opportunity_df = pd.read_excel(excel_path, sheet_name="Opportunity")
    product_df = pd.read_excel(excel_path, sheet_name="Product")
    for _, row in accounts_df.iterrows():
        

    # opportunities_df = pd.read_excel(excel_path, sheet_name=opportunities_sheet)
    # opportunities_df[id_column] = opportunities_df[id_column].astype(str)
    # accounts_df["Account Name"] = accounts_df["Account Name"].astype(str)

    # # Build base dict from accounts_info
    # result = {}
    # for _, acc_row in accounts_df.iterrows():
    #     acc_name = acc_row["Account Name"]
    #     acc_info = {k: v for k, v in acc_row.items() if k != "Account Name"}
    #     result[acc_name] = acc_info
    #     result[acc_name]["opportunities"] = {}

    # # Add opportunities under each account
    # for _, opp_row in opportunities_df.iterrows():
    #     opp_id = opp_row[id_column]
    #     opp_data = opp_row.drop(id_column).to_dict()
    #     for k, v in opp_data.items():
    #         if hasattr(v, 'isoformat'):
    #             opp_data[k] = str(v)
    #     acc_name = opp_data.get("Account Name", None)
    #     if acc_name and acc_name in result:
    #         result[acc_name]["opportunities"][opp_id] = opp_data
    #     else:
    #         # If account name not found, add under a special key
    #         if "Unknown" not in result:
    #             result["Unknown"] = {"opportunities": {}}
    #         result["Unknown"]["opportunities"][opp_id] = opp_data
    # return result

if __name__ == "__main__":
    excel_file = "data/C360.xlsx"
    accounts_dict = accounts_with_opportunities(excel_file)
    with open("opportunities_dict.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps(accounts_dict, indent=4, ensure_ascii=False))
    print("Saved opportunities_dict.txt with the extracted data.")
