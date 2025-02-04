URL: https://www.zillow.com/homedetails/2162-Radnor-Rd-North-Palm-Beach-FL-33408/46675881_zpid/
Error calling OpenAI API: 

You tried to access openai.ChatCompletion, but this is no longer supported in openai>=1.0.0 - see the README at https://github.com/openai/openai-python for the API.

You can run Downloading Grit CLI from https://github.com/getgrit/gritql/releases/latest/download/grit-x86_64-unknown-linux-gnu.tar.gz to automatically upgrade your codebase to use the 1.0.0 interface. 

Alternatively, you can pin your installation to the old version, e.g. Collecting openai==0.28
  Downloading openai-0.28.0-py3-none-any.whl.metadata (13 kB)
Requirement already satisfied: requests>=2.20 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from openai==0.28) (2.32.3)
Requirement already satisfied: tqdm in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from openai==0.28) (4.67.1)
Collecting aiohttp (from openai==0.28)
  Downloading aiohttp-3.11.11-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (7.7 kB)
Requirement already satisfied: charset-normalizer<4,>=2 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from requests>=2.20->openai==0.28) (3.4.1)
Requirement already satisfied: idna<4,>=2.5 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from requests>=2.20->openai==0.28) (3.10)
Requirement already satisfied: urllib3<3,>=1.21.1 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from requests>=2.20->openai==0.28) (2.3.0)
Requirement already satisfied: certifi>=2017.4.17 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from requests>=2.20->openai==0.28) (2025.1.31)
Collecting aiohappyeyeballs>=2.3.0 (from aiohttp->openai==0.28)
  Downloading aiohappyeyeballs-2.4.4-py3-none-any.whl.metadata (6.1 kB)
Collecting aiosignal>=1.1.2 (from aiohttp->openai==0.28)
  Downloading aiosignal-1.3.2-py2.py3-none-any.whl.metadata (3.8 kB)
Collecting async-timeout<6.0,>=4.0 (from aiohttp->openai==0.28)
  Downloading async_timeout-5.0.1-py3-none-any.whl.metadata (5.1 kB)
Collecting attrs>=17.3.0 (from aiohttp->openai==0.28)
  Downloading attrs-25.1.0-py3-none-any.whl.metadata (10 kB)
Collecting frozenlist>=1.1.1 (from aiohttp->openai==0.28)
  Downloading frozenlist-1.5.0-cp39-cp39-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (13 kB)
Collecting multidict<7.0,>=4.5 (from aiohttp->openai==0.28)
  Downloading multidict-6.1.0-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (5.0 kB)
Collecting propcache>=0.2.0 (from aiohttp->openai==0.28)
  Downloading propcache-0.2.1-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (9.2 kB)
Collecting yarl<2.0,>=1.17.0 (from aiohttp->openai==0.28)
  Downloading yarl-1.18.3-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (69 kB)
Requirement already satisfied: typing-extensions>=4.1.0 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from multidict<7.0,>=4.5->aiohttp->openai==0.28) (4.12.2)
Downloading openai-0.28.0-py3-none-any.whl (76 kB)
Downloading aiohttp-3.11.11-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (1.6 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.6/1.6 MB 145.1 MB/s eta 0:00:00
Downloading aiohappyeyeballs-2.4.4-py3-none-any.whl (14 kB)
Downloading aiosignal-1.3.2-py2.py3-none-any.whl (7.6 kB)
Downloading async_timeout-5.0.1-py3-none-any.whl (6.2 kB)
Downloading attrs-25.1.0-py3-none-any.whl (63 kB)
Downloading frozenlist-1.5.0-cp39-cp39-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl (242 kB)
Downloading multidict-6.1.0-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (124 kB)
Downloading propcache-0.2.1-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (208 kB)
Downloading yarl-1.18.3-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (321 kB)
Installing collected packages: propcache, multidict, frozenlist, attrs, async-timeout, aiohappyeyeballs, yarl, aiosignal, aiohttp, openai
  Attempting uninstall: openai
    Found existing installation: openai 1.61.0
    Uninstalling openai-1.61.0:
      Successfully uninstalled openai-1.61.0
Successfully installed aiohappyeyeballs-2.4.4 aiohttp-3.11.11 aiosignal-1.3.2 async-timeout-5.0.1 attrs-25.1.0 frozenlist-1.5.0 multidict-6.1.0 openai-0.28.0 propcache-0.2.1 yarl-1.18.3

A detailed migration guide is available here: https://github.com/openai/openai-python/discussions/742


URL: https://www.zillow.com/homedetails/630-Ocean-Dr-APT-308-Juno-Beach-FL-33408/46800761_zpid/
Error calling OpenAI API: 

You tried to access openai.ChatCompletion, but this is no longer supported in openai>=1.0.0 - see the README at https://github.com/openai/openai-python for the API.

You can run  to automatically upgrade your codebase to use the 1.0.0 interface. 

Alternatively, you can pin your installation to the old version, e.g. Requirement already satisfied: openai==0.28 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (0.28.0)
Requirement already satisfied: requests>=2.20 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from openai==0.28) (2.32.3)
Requirement already satisfied: tqdm in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from openai==0.28) (4.67.1)
Requirement already satisfied: aiohttp in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from openai==0.28) (3.11.11)
Requirement already satisfied: charset-normalizer<4,>=2 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from requests>=2.20->openai==0.28) (3.4.1)
Requirement already satisfied: idna<4,>=2.5 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from requests>=2.20->openai==0.28) (3.10)
Requirement already satisfied: urllib3<3,>=1.21.1 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from requests>=2.20->openai==0.28) (2.3.0)
Requirement already satisfied: certifi>=2017.4.17 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from requests>=2.20->openai==0.28) (2025.1.31)
Requirement already satisfied: aiohappyeyeballs>=2.3.0 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from aiohttp->openai==0.28) (2.4.4)
Requirement already satisfied: aiosignal>=1.1.2 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from aiohttp->openai==0.28) (1.3.2)
Requirement already satisfied: async-timeout<6.0,>=4.0 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from aiohttp->openai==0.28) (5.0.1)
Requirement already satisfied: attrs>=17.3.0 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from aiohttp->openai==0.28) (25.1.0)
Requirement already satisfied: frozenlist>=1.1.1 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from aiohttp->openai==0.28) (1.5.0)
Requirement already satisfied: multidict<7.0,>=4.5 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from aiohttp->openai==0.28) (6.1.0)
Requirement already satisfied: propcache>=0.2.0 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from aiohttp->openai==0.28) (0.2.1)
Requirement already satisfied: yarl<2.0,>=1.17.0 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from aiohttp->openai==0.28) (1.18.3)
Requirement already satisfied: typing-extensions>=4.1.0 in /opt/hostedtoolcache/Python/3.9.21/x64/lib/python3.9/site-packages (from multidict<7.0,>=4.5->aiohttp->openai==0.28) (4.12.2)

A detailed migration guide is available here: https://github.com/openai/openai-python/discussions/742


