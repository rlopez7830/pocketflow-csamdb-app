## Do NOT Create Master Routing Flow
- **Avoid** creating a single flow that branches based on request type
- Instead: Create specific flows (or use individual nodes) for each route
- Each route handler should directly call the relevant flow/node
- This keeps routes simple and maintainable

### ❌ WRONG: Master Routing Flow (Anti-pattern)

```python
# BAD: Don't do this!
class RouterNode(Node):
    def prep(self, shared):
        return shared["request_type"]
    
    def exec(self, request_type):
        return request_type
    
    def post(self, shared, prep_res, exec_res):
        # Branching based on request type
        if exec_res == "add":
            return "add"
        elif exec_res == "update":
            return "update"
        elif exec_res == "delete":
            return "delete"
        return "default"

# Creating a master flow with all branches
router_node = RouterNode()
add_node = AddTaskNode()
update_node = UpdateTaskNode()
delete_node = DeleteTaskNode()
save_flow = create_save_flow()

router_node - "add" >> add_node >> save_flow
router_node - "update" >> update_node >> save_flow
router_node - "delete" >> delete_node >> save_flow

master_flow = Flow(start=router_node)

# Using master flow in routes - TOO COMPLEX!
@app.post("/add")
async def add_task(name: str = Form(...)):
    shared["request_type"] = "add"
    shared["new_task"] = {"name": name}
    master_flow.run(shared)  # Overkill - runs routing logic unnecessarily
    return RedirectResponse(url="/", status_code=303)

@app.put("/update/{task_id}")
async def update_task(task_id: int, updates: TaskUpdate):
    shared["request_type"] = "update"
    shared["task_id"] = task_id
    shared["updates"] = updates.model_dump()
    master_flow.run(shared)  # Still using the same complex flow
    return JSONResponse({"success": True})
```

**Why this is bad:**
- Adds unnecessary complexity and indirection
- Poor separation of concerns

### ✅ CORRECT: Direct Flow/Node per Route

```python
# GOOD: Simple, direct approach

# Define your nodes
class AddTaskNode(Node):
    def prep(self, shared):
        return {"tasks": shared["tasks"], "new_task": shared["new_task"]}
    
    def exec(self, prep_data):
        task_id = generate_task_id(prep_data["tasks"])
        return {"id": task_id, **prep_data["new_task"], "completed": False}
    
    def post(self, shared, prep_res, exec_res):
        shared["tasks"].append(exec_res)
        return "default"

class UpdateTaskNode(Node):
    def prep(self, shared):
        return {"tasks": shared["tasks"], "task_id": shared["task_id"], 
                "updates": shared["updates"]}
    
    def exec(self, prep_data):
        return [
            {**task, **prep_data["updates"]} if task["id"] == prep_data["task_id"] else task
            for task in prep_data["tasks"]
        ]
    
    def post(self, shared, prep_res, exec_res):
        shared["tasks"] = exec_res
        return "default"

class DeleteTaskNode(Node):
    def prep(self, shared):
        return {"tasks": shared["tasks"], "task_id": shared["task_id"]}
    
    def exec(self, prep_data):
        return [task for task in prep_data["tasks"] 
                if task["id"] != prep_data["task_id"]]
    
    def post(self, shared, prep_res, exec_res):
        shared["tasks"] = exec_res
        return "default"

# Create a reusable save flow
prepare_node = PrepareDataNode()
write_node = WriteFileNode()
prepare_node >> write_node
save_flow = Flow(start=prepare_node)

# Create specific flows for each operation (node + save)
def create_add_task_flow():
    add_node = AddTaskNode()
    add_node >> save_flow
    return Flow(start=add_node)

def create_update_task_flow():
    update_node = UpdateTaskNode()
    update_node >> save_flow
    return Flow(start=update_node)

def create_delete_task_flow():
    delete_node = DeleteTaskNode()
    delete_node >> save_flow
    return Flow(start=delete_node)

# Create flow instances
add_task_flow = create_add_task_flow()
update_task_flow = create_update_task_flow()
delete_task_flow = create_delete_task_flow()

# Each route uses its specific flow
@app.post("/add")
async def add_task(name: str = Form(...), priority: str = Form(...)):
    shared["new_task"] = {"name": name, "priority": priority}
    
    # Run the add task flow (which includes saving)
    add_task_flow.run(shared)
    
    return RedirectResponse(url="/", status_code=303)

@app.put("/update/{task_id}")
async def update_task(task_id: int, updates: TaskUpdate):
    shared["task_id"] = task_id
    shared["updates"] = updates.model_dump(exclude_none=True)
    
    # Run the update task flow (which includes saving)
    update_task_flow.run(shared)
    
    return JSONResponse({"success": True})

@app.delete("/delete/{task_id}")
async def delete_task(task_id: int):
    shared["task_id"] = task_id
    
    # Run the delete task flow (which includes saving)
    delete_task_flow.run(shared)
    
    return JSONResponse({"success": True})
```

**Why this is better:**
- ✅ Clear and explicit - easy to see what each route does
- ✅ Routes are independent - can modify one without affecting others
- ✅ Follows single responsibility principle


# Adding AGS Authentication to a Web App

There is a library called 'ags-auth' that simplifies the process of ensuring a user has access to the app using Microsoft authentication and the associated Azure app's information. Please follow the steps below to add AGS authentication:

1. Add the ags-auth library to the requirements.txt file. It is located at https://github.com/intel-sandbox/ags-auth.git

2. Use the Git CLI to clone the repository into the current workspace and read the code and readme.md to understand how to use the library. Here is how to clone the repository:
   ```bash
   git clone https://github.com/intel-sandbox/ags-auth.git
   ```

3. In the web app, create a login endpoint (e.g., /login) that first checks if a valid token is provided by the user. If so, redirect the user to the main route '/'. Otherwise, redirect the user to the MSAL authorization URL. Set a state cookie to prevent CSRF attacks.

4. Create a callback endpoint (the REDIRECT_URI from config.yaml) that MSAL will redirect to after the user logs in. This endpoint should handle the token exchange and set the token as an HTTP-only cookie. It should also set an expiration time for the cookie based on the token's expiration time or, if that is not found, set it to 1 hour (also stored as a cookie). The callback should only set the relevant cookies if the user has been successfully authenticated and the user's groups match at least one of the Azure app assigned groups. If not, direct the user to an error page saying authentication failed. Check the value of the state cookie to prevent CSRF attacks and delete this cookie after checking its value.

5. Make every protected endpoint check for the presence of a token and validate it using the 'ags-auth' library. If the token is missing or invalid, redirect the user to the login endpoint.

6. Delete the cloned repository for ags-auth after the implementation is complete.

## Considerations
- DO NOT use MSAL or any Microsoft authentication libraries directly. Only use the 'ags-auth' library for all authentication-related tasks. It has everything needed to authenticate a user and validate their token.
- The config.yaml file with the Azure app details will be provided by the user in the workspace. Inside it, there will be a REDIRECT_URI provided. Use that as the auth callback endpoint and change the port and host of the app accordingly. DO NOT change anything in the config.yaml file.
- There is no need for a separate login page. Only the login endpoint is needed to handle authentication.
- There is no need to store any user info server side.