import cv2
import easyocr
import numpy as np
import streamlit as st
import re
import pymysql

st.set_page_config(layout="wide")

username=st.secrets['AWS_RDS_username']
password=st.secrets['AWS_RDS_password']
Endpoint=st.secrets['Endpoint']
Dbase=st.secrets['DATABASE']

# Establish a connection to the MySQL database
connection = pymysql.connect(
    host=Endpoint,
    user=username,
    password=password,
    database=Dbase
)
cursor = connection.cursor()

# Create a table for storing the extracted information
create_table_query = """
CREATE TABLE IF NOT EXISTS extracted_infos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image LONGBLOB,
    email VARCHAR(255),
    phone_numbers VARCHAR(255),
    address VARCHAR(255),
    card_holder_name VARCHAR(255),
    company_details TEXT,
    website_url VARCHAR(255),
    pin_code VARCHAR(10)
)
"""
cursor.execute(create_table_query)

# Store the extracted information in the MySQL database
def store_extracted_info(image,email, phone_numbers, address, card_holder_name, company_details, website_url, pin_code):
    img_bytes = cv2.imencode('.jpg', image)[1].tobytes()
    insert_query = """
    INSERT INTO extracted_infos (image,email, phone_numbers, address, card_holder_name, company_details, website_url, pin_code)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (img_bytes,email, ",".join(phone_numbers), address, card_holder_name, company_details, website_url, pin_code)
    cursor.execute(insert_query, values)
    connection.commit()

# Update the extracted information in the MySQL database

# Delete the extracted information from the MySQL database
def delete_extracted_info(id):
    delete_query = """DELETE FROM extracted_infos WHERE id = %s"""
    cursor.execute(delete_query, (id))
    connection.commit()


# Preprocessing steps with adjustable parameters
@st.cache_data
def preprocess_image(image, blur_kernel_size, threshold_block_size, threshold_c):
    # Resize the image to a reasonable resolution
    image = cv2.resize(image, (800, 600))
    
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (blur_kernel_size, blur_kernel_size), 0)
    
    # Binarization using adaptive thresholding
    binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, threshold_block_size, threshold_c)
    
    return binary

# Text extraction using easyOCR
@st.cache_data
def extract_text(image):
    reader = easyocr.Reader(['en'])
    results = reader.readtext(image)
    #confidences = reader.get_confidence(image)
    return results

# Main function
#@st.cache_data
def process_business_card(image):#, blur_kernel_size, threshold_block_size, threshold_c):

    # Extract text from the image and get confidences
    extracted_text = extract_text(image)
    confidences=[text[2] for text in extracted_text]
    
    # Check if the extracted text is empty
    if len(extracted_text) == 0:
        return None
    
    # Check the average confidence level
    average_confidence = np.mean(confidences)
    
    # If confidence is high, no further processing is required
    #if average_confidence > 0.75:
     #   return image, extracted_text

    while average_confidence < 0.75:
         
         st.info("Uploaded image is not of good quality. Try adjusting the parameters and processing it.")

         blur_kernel_size = st.slider("Blur Kernel Size", 3, 15, 5, step=2)
         threshold_block_size = st.slider("Threshold Block Size", 11, 41, 21, step=10)
         threshold_c = st.slider("Threshold Constant", -10, 10, 0, step=1)
        
    
         # Preprocess the image
         #processed_image = preprocess_image(image, blur_kernel_size, threshold_block_size, threshold_c)
         processed_image = preprocess_image(image, blur_kernel_size, threshold_block_size, int(threshold_c))

         st.subheader(":blue[Processed Image]")
         st.image(processed_image)

         extracted_text = extract_text(processed_image)
         confidences = [result[2] for result in extracted_text]
         average_confidence = np.mean(confidences)
    
    # Extract text from the processed image
         #extracted_text,confidences = extract_text(processed_image)
    
    # Extracted information
    email = ''
    phone_numbers = ''
    address = ''
    card_holder_name = ''
    designation=''
    company_details = ''
    website_url = ''
    pin_code = ''
    st.write(":green[:+1: The image is of goood quality. Further Image processing is not needed]")
    for text in extracted_text:
        result = text[1]
        if re.search(r'@', result.lower()):
            email = result.lower()
        elif re.search(r'(?:ph|phone|phno)?\s*(?:[+-]?\d\s*[\(\)]*){7,}', result):
            phone_numbers=(result)
        elif re.search(r'\d{6,7}', result.lower()):
            pin_code = re.search(r'\d{6,7}', result.lower()).group()
        elif re.match(r"(?!.*@)(www|.*com$)", result):
            website_url = result.lower()
        else:
            if not address and any(keyword in result.lower() for keyword in ['road', 'floor', ' st ', 'st,', 'street', ' dt ',
                                                                                 'district', 'near', 'beside', 'opposite',
                                                                                 ' at ', ' in ', 'center', 'main road',
                                                                                 'state', 'country', 'post', 'zip', 'city',
                                                                                 'zone', 'mandal', 'town', 'rural', 'circle',
                                                                                 'next to', 'across from', 'area',
                                                                                 'building', 'towers', 'village',
                                                                                 ' ST ', ' VA ', ' VA,', ' EAST ', ' WEST ',
                                                                                 ' NORTH ', ' SOUTH ']) or re.search(r'\d{6,7}',
                                                                                                                   result):
                address = result
            else:
                if len(result) >= 4 and ',' not in result and '.' not in result and 'www.' not in result:
                    if not re.match("^[0-9]{0,3}$", result) and not re.match("^[^a-zA-Z0-9]+$", result):
                        numbers = re.findall('\d+', result)
                        if len(numbers) == 0 or all(len(num) < 3 for num in numbers) and not any(
                                num in result for num in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] * 3):
                            if not card_holder_name:
                                card_holder_name = result
                            elif not designation:
                                words = result.split()
                                if len(words) >= 2:
                                  designation = ' '.join(words[:2])
                                  company_details = ' '.join(words[2:])
                                else:
                                  designation = result
                            else:
                                  company_details += result + '\n'
    

    return email, phone_numbers, address, card_holder_name, designation,company_details, website_url, pin_code

# Streamlit user interface
def main():
    st.title(":violet[Business Card Text Extraction]")
    
    col1,col2=st.columns(2)

    with col1:
    # File uploader for image selection
      uploaded_file = st.file_uploader(":blue[Upload a business card image]", type=["jpg", "jpeg", "png"])

      email = ''
      phone_numbers = []
      address = ''
      card_holder_name = ''
      designation=''
      company_details = ''
      website_url = ''
      pin_code = ''
    
      if uploaded_file is not None:
        # Read the uploaded image
        image = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), 1)
        #image=cv2.imread(image)
        
        # Parameters for image processing (with adjustable sliders)
       # blur_kernel_size = st.slider("Blur Kernel Size", 3, 15, 5, step=2)
        #threshold_block_size = st.slider("Threshold Block Size", 11, 41, 21, step=10)
        #threshold_c = st.slider("Threshold Constant", -10, 10, 0, step=1)
        
        # Process the business card image and extract text
        email, phone_numbers, address, card_holder_name,designation, company_details, website_url, pin_code = process_business_card(image)
        
        # Display the original image
        st.subheader(":blue[Original Image]")
        st.image(image)
        
        # Display the processed image
        #st.subheader("Processed Image")
        #st.image(processed_image, channels="BGR")
    
    with col2:  
        if uploaded_file is not None: 
        # Display the extracted information
           st.subheader("**:green[EXTRACTED INFORMATION]:**")
           st.write(":green[Card Holder Name:bust_in_silhouette::]   ", card_holder_name)
           st.write(":green[Designation:reminder_ribbon::   ]",designation)
           st.write(":green[Email :e-mail::    ]", email)
           st.write(":green[Phone Numbers:telephone_receiver::   ]", phone_numbers)
           st.write(":green[Address:house::  ]", address)
           st.write(":green[Pin Code:earth_asia::   ]", pin_code)
           st.write(":green[Company Details:office::    ]",company_details.strip())
           st.write(":green[Website URL:globe_with_meridians::  ]", website_url)
           

        
        # Database operations
        #st.subheader("Database Operations")
        
           col1, col2, col3 = st.columns(3)

        # Database operations
        
        
        
        # Store extracted information in the database
           if col1.button("Store Info"):
            store_extracted_info(image,email, phone_numbers, address, card_holder_name, company_details, website_url, pin_code)
            if store_extracted_info:
              st.success(":white_check_mark: Information stored in the database.")
        
        # Update extracted information in the database
           with col2:
              st.write("Update Info")
              cursor.execute("SELECT * FROM extracted_infos")
              extracted_info_list = cursor.fetchall()
              card_id = [info[0] for info in extracted_info_list]

              update_id=st.multiselect("id you want to update",card_id)
              if update_id:
                for id in update_id:
                  update_email = st.text_input(label="Enter new email")
                  update_phone_numbers = st.text_input( label="Enter new phone number")
                  update_address = st.text_area( label="Enter new address")
                  update_card_holder_name = st.text_input( label="Enter new card holder name")
                  update_company_details = st.text_input(label="Enter new company details")
                  update_website_url = st.text_input( label="Enter new website URL")
                  update_pin_code = st.text_input( label="Enter new pin code")
                  if st.button("update"):
               #update_extracted_info(update_id, update_email, update_phone_numbers,update_address, update_card_holder_name, update_company_details, update_website_url, update_pin_code)
                       cursor.execute(
                    "UPDATE extracted_infos SET email = %s, phone_numbers = %s, address = %s, card_holder_name = %s, company_details = %s, website_url = %s, pin_code = %s WHERE id = %s",
                    (update_email, update_phone_numbers, update_address, update_card_holder_name, update_company_details, update_website_url, update_pin_code, id)
                )
                       st.success(":white_check_mark: Information updated in the database.")
                  #except:
                   # st.error("Error occurred while updating the information.")
               
        # Delete extracted information from the database

           # Delete extracted information from the database
           
           with col3:
               st.write(' ')
               cursor.execute("SELECT * FROM extracted_infos")
               extracted_info_list = cursor.fetchall()
               card_id = [info[0] for info in extracted_info_list]
               st.write("select entries to delete") 
               selected_options = st.multiselect('', card_id)

               if st.button('DELETE SELECTED ENTRIES'):
                    for option in selected_options:
                       cursor.execute("DELETE FROM extracted_infos WHERE id = " +str(option))
                       connection.commit()
                       st.write("selected id deleted successfully")
                       st.write(' ')    

    
# Run the Streamlit application
if __name__ == "__main__":
    main()

