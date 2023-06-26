
# Business Card Text Extraction

This is a Python script that extracts information from business card images and stores it in a MySQL database. It utilizes the EasyOCR library for text extraction and OpenCV for image preprocessing. The extracted information includes email, phone numbers, address, card holder name, designation, company details, website URL, and pin code.

## Setup

1. Install the required libraries by running the following command:

   ```
   pip install opencv-python easyocr streamlit pymysql
   ```

2. Create a MySQL database named "business_card" or update the database name in the script accordingly.

3. Update the MySQL connection details (host, user, password) in the script to match your local setup.

4. Run the script using the following command:

   ```
   streamlit run script.py
   ```

5. The Streamlit web application will open in your browser. You can now upload business card images and extract information.

## Usage

1. Upload a business card image by clicking on the "Upload a business card image" button.

2. The script will process the image and extract the relevant information.

3. The original image and processed image will be displayed on the left side of the web interface.

4. The extracted information will be displayed on the right side of the web interface, including the card holder name, designation, email, phone numbers, address, pin code, company details, and website URL.

5. Database Operations:
   - Click the "Store Info" button to store the extracted information in the MySQL database.
   - To update information, select the entry ID from the "id you want to update" dropdown, enter the new information in the corresponding input fields, and click the "Update" button.
   - To delete entries, select the entry IDs from the "select entries to delete" multi-select dropdown and click the "DELETE SELECTED ENTRIES" button.

Note: Adjustments to image processing parameters can be made using the sliders provided.
