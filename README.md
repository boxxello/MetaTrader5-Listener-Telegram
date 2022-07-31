# MetaTrader5_Listener_Telegram

## SETUP

To install the py MT5 bot you can do it in some simple steps:
Python required version 3.9.

Check your py version by cmd:
```cmd
python3 -V
```


Check if pip is installed with:
```cmd
pip --version
```
If not, get it by:
```cmd
py -m ensurepip --upgrade
```

Then let's create a venv :

```cmd
  py -3.9 -m venv name_of_the_venv
```

Then we activate it by:
```cmd
\path\to\env\Scripts\activate
```
Some of the requirements of the bot need the pip upgrade,
otherwise it won't work based on MetaTrader5 deps on the
activated venv.
We can solve this by:
```cmd
py -m pip install --upgrade pip
```
Now let's install the deps, the first one we're going to install is: pymt5adapter.

We actually do that by:
```cmd
pip install -U pymt5adapter
```
This is a link to his repo: https://github.com/nicholishen/pymt5adapter .


Then we are going to install the other deps:
```cmd
pip install -r requirements.txt
```

## Setup of the user_data.env file
You need to provide all the requirements stated there.
<br>
Note:
If you're going to use multiple terminals I advice you to copy-paste the terminal in different folders and giving
the exact path to the user_data MT_EXE_PATH .env var.
You could also use different terminals, depending on your choice.

<br>
<br>
