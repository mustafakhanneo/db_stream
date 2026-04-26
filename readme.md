#### DBMS Streamlit App

## Setup Instructions

Follow these steps to set up and run the project locally.

### 1. Create `.env` File

In the root directory of the project, create a `.env` file and add the following environment variables:

````markdown

```env
DB_USER=avnadmin
DB_PASSWORD=AVPS_JL7VtHx7i3Ued87Ko6X
DB_HOST=mysql-3795b69f-mustafa.c.aivencloud.com
DB_PORT=24963
DB_NAME=defaultdb
DB_SSL_CA=ca.pem
````

### 2. Install Dependencies

Make sure you have Python installed, then install the required packages using:

```bash
pip install -r requirements.txt
```

### 3. Run the Application

Start the Streamlit app with:

```bash
streamlit run app.py
```

## Notes

* Ensure the `ca.pem` file is present in the project directory for SSL connection.
* It is recommended to use a virtual environment for dependency management.

```
```
