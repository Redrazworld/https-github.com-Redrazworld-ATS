import streamlit as st
import pandas as pd
import hashlib
import firebase_admin
from firebase_admin import credentials, db

# Check if Firebase app has already been initialized
if not firebase_admin._apps:
    # Initialize Firebase
    cred = credentials.Certificate("operationats-7e544-ed646f3db11f.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://operationats-7e544-default-rtdb.firebaseio.com/'
    })

# Define a function to generate session state
def get_session_id():
    return hashlib.sha256(str(st.session_state).encode()).hexdigest()

# Define a function to create or get session state
def create_or_get_session_state():
    session_id = get_session_id()
    if not hasattr(st, '_custom_session_state'):
        st._custom_session_state = {}
    if session_id not in st._custom_session_state:
        st._custom_session_state[session_id] = SessionState(_counter=0)
    return st._custom_session_state[session_id]

# Define the SessionState class
class SessionState(object):
    def _init_(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

@st.cache_data()
def read_order_data():
    try:
        ref = db.reference('orders')
        existing_data = ref.get()
        existing_df = pd.DataFrame(existing_data).transpose()
        if not existing_df.empty:
            existing_df["Order Date"] = pd.to_datetime(existing_df["Order Date"]).dt.strftime('%Y-%m-%d')
            existing_df["Delivery Date"] = pd.to_datetime(existing_df["Delivery Date"]).dt.strftime('%Y-%m-%d')
        return existing_df
    except Exception as e:
        st.error(f"An error occurred while reading the order data: {e}")
        return pd.DataFrame()

def create_order():
    emp_id = st.text_input("Employee ID")
    customer_name = st.text_input("Customer Name")
    contact_number = st.text_input("Contact Number")
    order_date = st.date_input("Order Date")
    delivery_date = st.date_input("Delivery Date")
    product_id = st.text_input("Product ID")
    quantity = st.number_input("Quantity", min_value=0)
    price = st.number_input("Price", min_value=0)

    total_price = quantity * price

    if st.button("Save Order"):
        try:
            contact_number = int(contact_number)
            order_data = {
                "Emp ID": emp_id,
                "Customer Name": customer_name,
                "Contact Number": contact_number,
                "Order Date": order_date.strftime('%Y-%m-%d'),
                "Delivery Date": delivery_date.strftime('%Y-%m-%d'),
                "Product ID": product_id,
                "Quantity": quantity,
                "Price": price,
                "Total Price": total_price
            }

            ref = db.reference('orders')
            ref.push(order_data)

            st.success("Order saved successfully!")
        except ValueError:
            st.error("Contact Number must be an integer.")
        except Exception as e:
            st.error(f"An error occurred while saving the order: {e}")

def delivery_update():
    contact_number = st.text_input("Enter Contact Number")

    if contact_number:
        order_df = read_order_data()

        contact_number = int(contact_number)

        # Check if the column exists in the DataFrame
        if "Contact Number" in order_df.columns:
            # Use the column name as it is
            contact_column = "Contact Number"
        elif "Customer Phone" in order_df.columns:
            # Use alternative column name if available
            contact_column = "Customer Phone"
        else:
            st.error("Contact Number column not found in records!")
            st.write("Available columns:", order_df.columns.tolist())
            return

        matching_rows = order_df[order_df[contact_column] == contact_number]

        if not matching_rows.empty:
            st.write("Matching Rows:")
            st.write(matching_rows)

            row_index = st.number_input("Enter the row index to update", min_value=0, max_value=len(matching_rows)-1)

            if row_index < len(matching_rows):
                row = matching_rows.iloc[row_index]
                
                amount_received = st.number_input(f"Enter Amount Received for Row {row_index}", value=row.get("Amount Received", 0))
                payment_status = st.selectbox(f"Payment Status for Row {row_index}", ["Online", "Cash"], index=0 if row.get("Payment Status") == "Online" else 1)
                delivery_status = st.selectbox(f"Delivery Status for Row {row_index}", ["Done", "Pending", "Cancel", "Full Payment", "Half Payment"], index=0 if row.get("Delivery Status") == "Done" else 1)
                remark = st.text_input(f"Remark for Row {row_index}")

                if st.button(f"Save/Update for Row {row_index}"):
                    doc_id = matching_rows.iloc[row_index].name
                    order_ref = db.reference(f'orders/{doc_id}')
                    order_ref.update({
                        "Amount Received": amount_received,
                        "Payment Status": payment_status,
                        "Delivery Status": delivery_status,
                        "Remark": remark
                    })

                    st.success("Delivery status and product updated successfully!")
            else:
                st.error(f"Row index {row_index} not found for the entered Contact Number!")
        else:
            st.error("Contact Number not found in records!")

def main():
    st.title("Order Management System")

    options = {
        "PO Form": create_order,
        "Delivery Updates": delivery_update
    }

    selection = st.sidebar.radio("Select Functionality", list(options.keys()))

    options[selection]()

if __name__ == "__main__":
    main()
