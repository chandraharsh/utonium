# [Utonium](https://github.com/chandraharsh/utonium/blob/master/README.md)

a project made with sugar, spice and everything nice and dubious amounts of Chemical X

**Stock Viewer** only works for NSE stocks as of now, BSE to come soon :stuck_out_tongue_closed_eyes:

`git clone https://github.com/chandraharsh/utonium.git` the repository

`cd utonium\app`

`git pull` just to be on the safe side

Create a virtual environment by runnig the command `python -m venv venv` within the `app` folder

`venv\Scripts\activate` to activate the virtual environment

`pip install -r requirements.txt` to install the necessary requirements

Update the run.bat file to match the paths to the project folder and run the **run.bat** to start the server.

if you wish to access the website over your local network in the **run.bat** replace `python index.py` command with `waitress-serve --port=6666 index:server`

Go to the above address to view the application, happy hunting :smiley:

**P.S : The application is to aimed to be run for personal use and locally on windows machine**
