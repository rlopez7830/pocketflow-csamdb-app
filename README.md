<h1 align="center">Github copilot template for agentic coding</h1>

This is a project template is based on [Pocket Flow](https://github.com/The-Pocket/PocketFlow), a 100-line LLM framework which used 

It is customised to work with Github Copilot and intel azure openai

# Steps to success
- Switch to plan mode and select Claude Opus  with thinking for the intial plan, If Claude Thinking is not available use the GPT 5 or Claude 4.5 it has sufficient reasoning capabiltiies. 

- give a high level description of what you want to do, finish with the following line
```
Please review this idea critically and come back to me with any questions before staring the system design.
```
-Then switch to agent mode:
```
Looks good. Please fill out the design.md template. Do not write any code until this step is completed.
```
- Once you have finished reviewing the design, ask it to implement it.
```
The design looks good please implement this code.
```

- To keep your code development well organize - separate each aspect of your work into individual chats. For example when you are first coding, please use a single chat to do design, implementation, and testing. At the end of your chat, please ask Copilot to summarize the changes and amend the design document so that only the latest version of the design remains in the repository. After that when you are attempting a refactoring/redesign/feature addition - create a separate chat and a separate branch for that, otherwise you will end up with a massive spaghetti of changes that will be impossible for your agent to parse productively. 


- For diagnostics and trouble-shooting in later sessions. Always create a markdown of the chat and put it into the docs directory as "GitHub_Copilot_Chat_Session_<your_user_id>". This way you will be able to share your chat history with others in your development team. You can just ask Copilot to create a markdown summary of the key aspects of the chat. 



- We have included rules files for various AI coding assistants to help you build LLM projects:
  - Configuration in [.github](.github) for GitHub Copilot
  - Download more chat modes and prompts from [Awesome Copilot](https://github.com/github/awesome-copilot/)
  
- Want to learn how to build LLM projects with Agentic Coding?

  - Check out the [Agentic Coding Guidance](https://the-pocket.github.io/PocketFlow/guide.html)
    
  - Check out the [YouTube Tutorial](https://www.youtube.com/@ZacharyLLM?sub_confirmation=1)

# Semgrep is setup  
We have added a semgrep security scan to automatically review your code after each PR. Please follow branch discipline and protect your main branch and use Pull Requests to merge into the main branch.

For the semgrep to be easy to track - you will need an IAPM. If you are in FQRL - contact sunil.sainis@intel.com for help. If you are not in FQRL - please contact your department's resource to get an IAPM you can use. 
