# MQTT IoT Gateway Communication Simulator

This project simulates a scenario where multiple IoT gateways communicate with a cloud-based MQTT broker to send and receive messages. It also includes functionality for authenticating the gateways, publishing messages, retrieving stored messages from a database, analyzing the data, and visualizing the results.

## Table of Contents

1. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
2. [Usage](#usage)
3. [Project Structure](#project-structure)
4. [Key Features](#key-features)
5. [Data Visualization](#data-visualization)
6. [Contributing](#contributing)
7. [License](#license)
8. [Contact](#contact)

## Getting Started

### Prerequisites

- Python 3.7 or later.
- The following Python libraries:
  - paho-mqtt
  - PyJWT
  - numpy
  - pymongo
  - matplotlib

You can install these libraries using the following command:

```bash
pip install -r requirements.txt
```

### Installation
```bash
git clone https://github.com/your-username/your-repo.git
```

Navigate to the project directory:
```bash
cd stratosfy_stress_testing
```

Install the required libraries:
```bash
pip install -r requirements.txt
```

## Usage
To run the simulator, execute the following command in the project directory:

```bash
python core.py
```

## Project Structure
- `core.py`: The main script to run the simulator.
- `requirements.txt`: Contains the list of necessary Python libraries.
- `credentials.txt`: (Not included in the repository for security reasons) Contains the credentials for gateways and database access.
- `/data`: Directory to store the generated CSV files and plots.

## Key Features
- Gateway Simulation: Simulates the operation of multiple IoT gateways.
- MQTT Communication: Handles the MQTT communication between the gateways and the cloud broker.
- Authentication: Authenticates the gateways using JWT tokens.
- Message Publishing: Publishes generated messages to specified MQTT topics.
- Database Retrieval: Retrieves stored messages from a MongoDB database based on a specified time range.
- Data Analysis: Analyzes the message data to calculate various metrics.
- Result Saving: Saves the results to CSV files.
- Data Visualization: Generates scatter plots to visualize the message timestamp distribution.

## Data Visualization
The project generates scatter plots to visualize the distribution and frequency of message timestamps, helping to analyze the system's performance.

## Contributing
Contributions are welcome! Please read the contributing guidelines to get started.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Contact
- Behrad Moeini - [behradmoeini@gmail.com](mailto:behradmoeini@gmail.com)
- Project Link: [https://github.com/behradmoeini/stratosfy_stress_testing](https://github.com/behradmoeini/stratosfy_stress_testing)
