## Do NOT Create Master Routing Flow
- **Avoid** creating a single flow that branches based on command type
- Instead: Create specific flows (or use individual nodes) for each command
- Each command handler should directly call the relevant flow/node
- This keeps commands simple and maintainable

### ❌ WRONG: Master Routing Flow (Anti-pattern)

```python
# BAD: Don't do this!
class RouterNode(Node):
    def prep(self, shared):
        return shared["command"]
    
    def exec(self, command):
        return command
    
    def post(self, shared, prep_res, exec_res):
        # Branching based on command type
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

# Using master flow in CLI - TOO COMPLEX!
def main():
    parser = argparse.ArgumentParser(description="Task Manager CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("name", help="Task name")
    add_parser.add_argument("--priority", default="medium", help="Task priority")
    
    update_parser = subparsers.add_parser("update", help="Update a task")
    update_parser.add_argument("task_id", type=int, help="Task ID")
    update_parser.add_argument("--name", help="New task name")
    
    args = parser.parse_args()
    shared = load_shared_store()
    
    # Setting command in shared and using master flow - Overkill!
    shared["command"] = args.command
    
    if args.command == "add":
        shared["new_task"] = {"name": args.name, "priority": args.priority}
    elif args.command == "update":
        shared["task_id"] = args.task_id
        shared["updates"] = {"name": args.name} if args.name else {}
    
    master_flow.run(shared)  # Runs routing logic unnecessarily
    print(f"✓ Command '{args.command}' completed")
```

**Why this is bad:**
- Adds unnecessary complexity and indirection
- Poor separation of concerns

### ✅ CORRECT: Direct Flow/Node per Command

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

# Each command uses its specific flow
def main():
    parser = argparse.ArgumentParser(description="Task Manager CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("name", help="Task name")
    add_parser.add_argument("--priority", default="medium", help="Task priority")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update a task")
    update_parser.add_argument("task_id", type=int, help="Task ID")
    update_parser.add_argument("--name", help="New task name")
    update_parser.add_argument("--priority", help="New priority")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("task_id", type=int, help="Task ID")
    
    args = parser.parse_args()
    
    # Initialize shared store
    shared = load_shared_store()
    
    # Each command directly calls its specific flow
    if args.command == "add":
        shared["new_task"] = {"name": args.name, "priority": args.priority}
        add_task_flow.run(shared)
        print(f"✓ Added task: {args.name}")
        
    elif args.command == "update":
        shared["task_id"] = args.task_id
        shared["updates"] = {k: v for k, v in vars(args).items() 
                           if k not in ["command", "task_id"] and v is not None}
        update_task_flow.run(shared)
        print(f"✓ Updated task {args.task_id}")
        
    elif args.command == "delete":
        shared["task_id"] = args.task_id
        delete_task_flow.run(shared)
        print(f"✓ Deleted task {args.task_id}")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

**Why this is better:**
- ✅ Clear and explicit - easy to see what each command does
- ✅ Commands are independent - can modify one without affecting others
- ✅ Follows single responsibility principle
