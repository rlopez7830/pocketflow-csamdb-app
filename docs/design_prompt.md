# Manufacturing CSAM Image Lookup Web App – Requirements

I am trying to build a FastAPI web app with Swagger UI documentation. The application will take a user-provided **Visual ID (VID)** representing a unit ID and display the corresponding **manufacturing assembly inline CSAM image** in the UI.

The application workflow should be:
1. User enters a VID in the web UI.
2. Backend uses that VID to query manufacturing history data from the database.
3. The backend uses **PyUber** to execute SQL queries against the manufacturing database.
4. The SQL query must first retrieve the necessary lot history information for that VID, including the attributes needed to locate the image:
   - Workweek processed
   - Operation
   - Tool
   - Lot / VID identifier
5. Using those returned attributes, the backend constructs the image storage path.
6. The backend uses Python to locate, load, and process the image.
7. The image is displayed inline in the UI.

An example image location may look like:

`\\atdfile1\dfM_IMAGE\WW10_2026\3040\CSM020\D609A810`

In this example:
- `WW10_2026` is the workweek folder
- `3040` is the operation
- `CSM020` is the tool
- `D609A810` is the VID / lot folder

The app should be robust, well-structured, and have high quality Swagger/OpenAPI documentation.

---

## Web App Route Description

The web app should have the following routes:

1. `"/"` — Main UI where the user enters the VID and views the image
2. `"/docs"` — Swagger UI for API documentation
3. `"/health"` — Health check endpoint
4. `"/lookup"` — Accepts a VID, queries manufacturing history, resolves the image path, and returns the image or image metadata
5. `"/image/{vid}"` — Returns the resolved CSAM image for a specific VID, if available

---

## UI Description

In the UI the user will:

1. Enter a **VID** into a text input box
2. Click a **Lookup** button
3. Wait for the backend to:
   - Query manufacturing history
   - Resolve the image location
   - Load the image
4. View the resulting **CSAM image inline**
5. See clear error messages if:
   - The VID is not found
   - The image path cannot be resolved
   - The image file is missing or unreadable
   - The database query fails

Please design the frontend using HTML, JavaScript, and Jinja2 templates as needed.

---

## Backend Description

When the user submits a VID:

1. Backend receives the VID from the UI
2. Backend uses **PyUber** to connect to the manufacturing database
3. Backend executes a SQL query to retrieve the manufacturing lot history for that VID
4. The query must extract the attributes needed to construct the image path:
   - Workweek / week processed
   - Operation
   - Tool name
   - Lot or VID identifier
5. Backend constructs the expected file path for the CSAM image
6. Backend uses Python to:
   - Check whether the file exists
   - Load the image
   - Convert or preprocess it if needed for display
7. Backend returns the image to the frontend for inline display

---

## Processing Logic Specifications

### Database Querying
- Use **PyUber** for all database access
- Query manufacturing lot history first
- Do not assume the image location is known before querying the database
- The database lookup must determine the correct:
  - Workweek
  - Operation
  - Tool
  - VID / lot folder

### Image Resolution
- Construct the image path only after the manufacturing metadata is returned
- Use Python to handle path joining safely
- The app should support UNC-style network paths
- The app should gracefully handle missing files and return a user-friendly error

### Image Handling
- Load the CSAM image from disk or network share
- Support common image formats if applicable
- Display the image inline in the browser
- If needed, resize or convert the image for web display

---

## User Experience Requirements

### Progress Feedback
- Show a loading indicator while:
  - The database is being queried
  - The image path is being resolved
  - The image is being loaded
- Display a status message such as:
  - “Querying manufacturing history…”
  - “Resolving image location…”
  - “Loading image…”

### Error Handling
- Validate the VID input before processing
- Return clear messages for:
  - Missing VID input
  - VID not found in the database
  - Image file not found
  - Database connection error
  - Unexpected processing errors

### Display Behavior
- Show the image inline on the page after lookup
- If the image cannot be found, show an informative message instead of failing silently

---

## Technical Requirements

### Core Framework
- Use **FastAPI** for the backend
- Use **Jinja2** for HTML templating
- Use **JavaScript** for UI interactions
- Use **PyUber** for database querying
- Use Python standard libraries and common image-processing libraries as needed

### Code Organization
- Keep database logic, path resolution, and image processing in separate utility functions or modules
- Follow PEP8 style guide
- Include docstrings for all functions
- Use clear and descriptive variable names

### Swagger/OpenAPI Documentation
- Provide strong documentation for all endpoints
- Include:
  - Request parameters
  - Response formats
  - Example request/response payloads
  - Error responses
- Ensure the API docs clearly explain that the VID is used to resolve the manufacturing metadata and image path

---

## Example Data Flow

1. User enters VID: `D609A810`
2. Backend queries manufacturing history using PyUber
3. Backend retrieves:
   - Workweek: `WW10_2026`
   - Operation: `3040`
   - Tool: `CSM020`
4. Backend constructs image path:

`\\atdfile1\dfM_IMAGE\WW10_2026\3040\CSM020\D609A810`

5. Backend loads the CSAM image
6. UI displays the image inline

---

## Example Error Conditions

If the VID does not exist:
- Return: “No manufacturing history found for VID X”

If the image file is missing:
- Return: “Image not found at the resolved location”

If database access fails:
- Return: “Unable to query manufacturing history at this time”

---

## Implementation Notes

- Use a clean separation between:
  - VID input handling
  - SQL lookup via PyUber
  - Image path resolution
  - Image loading/display
- The app should be easy to extend if additional metadata or alternate image locations need to be supported later
- The frontend should be simple and responsive

---

## Desired Output

Please generate a FastAPI web application scaffold that includes:
- A main HTML UI for VID lookup
- Swagger/OpenAPI documentation
- Backend VID lookup via PyUber
- Image path resolution logic
- Inline display of the resolved CSAM image
- Clear error handling and user feedback