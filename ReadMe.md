# Apache Airflow Installation

This guide will walk you through the steps to install Apache Airflow and configure the database details.

## Prerequisites

Before you begin, make sure you have the following prerequisites:

- Python (version X.X.X or higher)
- Pip (version X.X.X or higher)
- PostgreSQL (version X.X.X or higher)

## Installation

1. Clone the Apache Airflow repository:

    ```bash
    git clone https://github.com/apache/airflow.git
    ```

2. Change to the airflow directory:

    ```bash
    cd airflow
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Configure the database details in the `airflow.cfg` file:

    ```bash
    [core]
    sql_alchemy_conn = postgresql+psycopg2://username:password@localhost:5432/airflow

    [webserver]
    secret_key = your_secret_key
    ```

    Replace `username`, `password`, and `your_secret_key` with your actual database credentials and secret key.

5. Initialize the database:

    ```bash
    airflow db init
    ```

6. Start the Airflow web server:

    ```bash
    airflow webserver
    ```

7. Access the Airflow web interface by opening http://localhost:8080 in your web browser.

## Configuration

For more advanced configuration options, refer to the [Airflow documentation](https://airflow.apache.org/docs/).


## Airflow commands

To check the installed version of Apache Airflow by running the following command in your terminal

```bash
airflow version
```