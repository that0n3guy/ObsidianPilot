# Complete Guide to the Obsidian Local REST API

## Introduction: Understanding the Obsidian Local REST API

Imagine you're working with Obsidian, your trusted note-taking application, and you wish you could automate certain tasks or integrate it with other tools in your workflow. Perhaps you want to automatically create notes from web content, sync information with a task manager, or build a custom dashboard that pulls data from your vault. This is exactly where the Obsidian Local REST API comes into play.

The Local REST API plugin transforms Obsidian from a standalone application into a programmable platform. It creates a secure web server within Obsidian that listens for requests from other applications, allowing them to read, create, modify, and manage your notes programmatically. Think of it as adding a remote control to Obsidian - instead of clicking buttons and typing manually, other programs can send commands to perform these actions automatically.

## Core Concepts and Architecture

Before diving into the specific endpoints, let's understand how this system works at a fundamental level.

### The REST API Model

REST (Representational State Transfer) is a standardized way for different software systems to communicate over HTTP. In our case, the plugin creates a local web server that runs inside Obsidian, typically on port 27124. This server accepts HTTP requests from other applications and translates them into actions within your Obsidian vault.

The communication follows a request-response pattern:
1. An external application sends an HTTP request to the API
2. The request includes an API key for authentication
3. The plugin processes the request and performs the action in Obsidian
4. A response is sent back with the results or confirmation

### Security Architecture

Security is paramount when exposing your personal notes to external access. The plugin implements two layers of protection:

**HTTPS Encryption**: All communication is encrypted using SSL/TLS, even though it's local. The plugin generates a self-signed certificate on first run. While browsers may warn about this certificate (since it's not from a recognized authority), it still provides encryption for your data.

**API Key Authentication**: Every request must include a valid API key in the headers. This key is generated when you enable the plugin and acts as a password. Without this key, no external application can access your vault.

### Data Formats and Responses

The API uses standard web formats for data exchange:
- **JSON**: For structured data like note metadata, search results, and configuration
- **Plain text/Markdown**: For note content
- **URL encoding**: For file paths and special characters in parameters

## Complete Endpoint Documentation

Now let's explore every endpoint available in the API, organized by functional category.

### System Endpoints

These endpoints provide information about the API server itself and don't require specific vault operations.

#### GET / - Server Information
Returns basic details about the server and your authentication status.

**Purpose**: This endpoint serves as a health check and provides version information. It's the only endpoint that doesn't require authentication, making it useful for testing connectivity.

**Response Example**:
```json
{
  "authenticated": true,
  "ok": "running",
  "service": "Obsidian Local REST API",
  "versions": {
    "obsidian": "1.4.5",
    "self": "1.0.0"
  }
}
```

#### GET /obsidian-local-rest-api.crt - SSL Certificate
Returns the self-signed certificate used by the API.

**Purpose**: Allows clients to download and trust the certificate, eliminating browser warnings.

#### GET /openapi.yaml - API Specification
Returns the complete OpenAPI specification describing all endpoints.

**Purpose**: Provides machine-readable API documentation that tools can use to generate client libraries or interactive documentation.

### Active File Operations

These endpoints work with whatever file you currently have open in Obsidian's editor.

#### GET /active/ - Read Active File
Returns the content of the currently active file.

**Headers**:
- `Accept: application/vnd.olrapi.note+json` - Returns JSON with metadata
- Default - Returns raw markdown content

**JSON Response Structure**:
```json
{
  "content": "# My Note\nThis is the content...",
  "frontmatter": {
    "title": "My Note",
    "tags": ["example", "guide"]
  },
  "path": "folder/my-note.md",
  "stat": {
    "ctime": 1634567890,
    "mtime": 1634567900,
    "size": 1234
  },
  "tags": ["#example", "#guide"]
}
```

#### PUT /active/ - Replace Active File Content
Completely replaces the content of the active file.

**Request Body**: The new content as plain text
**Content-Type**: `text/markdown` for notes

#### POST /active/ - Append to Active File
Adds content to the end of the currently active file.

**Request Body**: Content to append
**Use Case**: Adding quick notes or logs without overwriting existing content

#### PATCH /active/ - Partially Update Active File
Surgically modifies specific sections of the active file.

**Headers**:
- `Operation`: `append`, `prepend`, or `replace`
- `Target-Type`: `heading`, `block`, or `frontmatter`
- `Target`: The specific target (heading path, block ID, or frontmatter field)
- `Target-Delimiter`: Separator for nested headings (default: `::`)

**Example - Append to a heading**:
```
Operation: append
Target-Type: heading
Target: Daily Notes::Tasks
Body: - [ ] New task item
```

#### DELETE /active/ - Delete Active File
Removes the currently active file from the vault.

**Warning**: This operation is irreversible through the API.

### Command Execution

These endpoints allow you to trigger Obsidian's built-in commands programmatically.

#### GET /commands/ - List Available Commands
Returns all commands available in your Obsidian instance.

**Response Example**:
```json
{
  "commands": [
    {
      "id": "editor:toggle-bold",
      "name": "Toggle bold"
    },
    {
      "id": "workspace:split-vertical",
      "name": "Split vertically"
    }
  ]
}
```

#### POST /commands/{commandId}/ - Execute Command
Triggers a specific Obsidian command.

**Parameters**:
- `commandId`: The command identifier (from the list endpoint)

**Use Cases**: Automating UI actions, triggering plugin commands, changing workspace layouts

### File Opening

#### POST /open/{filename} - Open File in UI
Opens a specified file in the Obsidian interface.

**Parameters**:
- `filename`: Path to the file relative to vault root
- `newLeaf` (optional): Open in new pane if true

**Purpose**: Useful for automation scripts that need to direct user attention to specific notes.

### Periodic Notes Management

These endpoints provide specialized handling for daily, weekly, monthly, quarterly, and yearly notes.

#### GET /periodic/{period}/ - Get Current Periodic Note
Retrieves today's/this week's/this month's periodic note.

**Parameters**:
- `period`: `daily`, `weekly`, `monthly`, `quarterly`, or `yearly`

#### GET /periodic/{period}/{year}/{month}/{day}/ - Get Specific Periodic Note
Retrieves a periodic note for a specific date.

**Parameters**:
- `period`: The period type
- `year`: Four-digit year
- `month`: Month (1-12)
- `day`: Day (1-31)

**Note**: The plugin uses your configured periodic note templates and folder settings.

#### PUT /periodic/{period}/ - Update Current Periodic Note
Replaces the content of the current periodic note.

#### PUT /periodic/{period}/{year}/{month}/{day}/ - Update Specific Periodic Note
Replaces the content of a specific periodic note.

#### POST /periodic/{period}/ - Append to Current Periodic Note
Adds content to the current periodic note (creates if necessary).

#### POST /periodic/{period}/{year}/{month}/{day}/ - Append to Specific Periodic Note
Adds content to a specific periodic note.

#### PATCH /periodic/{period}/ - Partially Update Current Periodic Note
Modifies specific sections using the same header system as active file patches.

#### PATCH /periodic/{period}/{year}/{month}/{day}/ - Partially Update Specific Periodic Note
Modifies specific sections of a dated periodic note.

#### DELETE /periodic/{period}/ - Delete Current Periodic Note
Removes the current periodic note.

#### DELETE /periodic/{period}/{year}/{month}/{day}/ - Delete Specific Periodic Note
Removes a specific periodic note.

### Search Operations

The search endpoints provide powerful ways to find content in your vault.

#### POST /search/ - Advanced Search
Performs complex searches using different query languages.

**Content-Type Options**:

1. **Dataview DQL** (`application/vnd.olrapi.dataview.dql+txt`):
   ```
   TABLE time-played, rating
   FROM #games
   WHERE rating > 4
   SORT rating DESC
   ```

2. **JsonLogic** (`application/vnd.olrapi.jsonlogic+json`):
   ```json
   {
     "and": [
       {"in": ["#project", {"var": "tags"}]},
       {">": [{"var": "frontmatter.priority"}, 3]}
     ]
   }
   ```

**Special JsonLogic Operators**:
- `glob`: Pattern matching (e.g., `{"glob": ["*.md", {"var": "path"}]}`)
- `regexp`: Regular expression matching

#### POST /search/simple/ - Simple Text Search
Performs a basic text search across all notes.

**Parameters**:
- `query`: The search term
- `contextLength`: Characters of context around matches (default: 100)

**Response Example**:
```json
[
  {
    "filename": "projects/web-app.md",
    "matches": [
      {
        "match": {"start": 150, "end": 165},
        "context": "...working on the REST API integration for our..."
      }
    ],
    "score": 0.95
  }
]
```

### Vault Directory Operations

These endpoints allow you to browse the folder structure of your vault.

#### GET /vault/ - List Root Directory
Lists all files and folders in the vault root.

**Response Example**:
```json
{
  "files": [
    "README.md",
    "daily/",
    "projects/",
    "archive/"
  ]
}
```

#### GET /vault/{pathToDirectory}/ - List Specific Directory
Lists contents of a specific directory.

**Parameters**:
- `pathToDirectory`: Path relative to vault root

**Note**: Empty directories are not returned, following Obsidian's model.

### Vault File Operations

These endpoints provide complete file management capabilities.

#### GET /vault/{filename} - Read File
Retrieves the content of any file in your vault.

**Parameters**:
- `filename`: Path relative to vault root

**Headers**:
- `Accept: application/vnd.olrapi.note+json` - Returns JSON with metadata
- Default - Returns raw content

#### PUT /vault/{filename} - Create or Update File
Creates a new file or completely replaces an existing one.

**Parameters**:
- `filename`: Target path (directories created automatically)

**Request Body**: File content
**Content-Type**: `text/markdown` for notes, appropriate type for other files

#### POST /vault/{filename} - Append to File
Adds content to the end of a file (creates if doesn't exist).

**Use Case**: Building up notes incrementally, logging entries

#### PATCH /vault/{filename} - Partially Update File
Modifies specific sections of a file using the same targeting system as active file patches.

**Headers**:
- `Operation`: `append`, `prepend`, or `replace`
- `Target-Type`: `heading`, `block`, or `frontmatter`
- `Target`: The specific target
- `Content-Type`: `text/markdown` or `application/json` (for structured data)

**Advanced Example - Update table via block reference**:
```
Operation: append
Target-Type: block
Target: ^table123
Content-Type: application/json
Body: [["New York", "8,336,817"], ["Los Angeles", "3,898,747"]]
```

#### DELETE /vault/{filename} - Delete File
Permanently removes a file from the vault.

**Warning**: No recycle bin - deletion is immediate and permanent.

## Practical Implementation Patterns

### Authentication Setup

Every request (except GET /) requires authentication. Include your API key in the Authorization header:

```http
Authorization: Bearer YOUR-API-KEY-HERE
```

### Working with File Paths

File paths in the API are always relative to your vault root and use forward slashes:
- Correct: `projects/2024/january/goals.md`
- Incorrect: `projects\2024\january\goals.md`
- Incorrect: `/projects/2024/january/goals.md`

### Handling Special Characters

When passing file paths or heading names in URLs, encode special characters:
- Space → `%20`
- Hash → `%23`
- Unicode → URL encode (e.g., `é` → `%C3%A9`)

### Error Handling

The API returns standard HTTP status codes:
- `200`: Success
- `204`: Success (no content)
- `400`: Bad request (check your parameters)
- `404`: File or resource not found
- `405`: Method not allowed (e.g., trying to update a directory)

Error responses include details:
```json
{
  "errorCode": 40404,
  "message": "File 'nonexistent.md' does not exist"
}
```

## Advanced Use Cases

### Building a Knowledge Graph Analyzer

Combine search and file reading to analyze note connections:
1. Use `/search/` with JsonLogic to find all notes with specific tags
2. Read each note with `/vault/{filename}` to extract links
3. Build a graph structure of connections
4. Generate visualization or statistics

### Automated Daily Journaling

Create a script that:
1. Uses `/periodic/daily/` POST to add entries
2. Reads calendar events and adds them as tasks
3. Pulls weather data and adds it to frontmatter
4. Commits changes to version control

### Smart Note Templates

Implement dynamic templates:
1. Read template with metadata using `/vault/{template}.md`
2. Execute searches to find related notes
3. Generate new content with contextual information
4. Create new note with `/vault/{filename}` PUT

### Cross-Platform Quick Capture

Build a web service that:
1. Accepts input from various sources (email, SMS, web forms)
2. Processes and formats the content
3. Uses `/vault/{inbox}/capture-{timestamp}.md` PUT to create notes
4. Optionally opens the note with `/open/{filename}`

## Best Practices and Considerations

### Performance Optimization

When working with many files:
- Batch operations where possible
- Cache frequently accessed data
- Use specific paths rather than searching when you know the location
- Limit search result sizes with appropriate queries

### Security Recommendations

1. **Protect Your API Key**: Never commit it to version control or share it publicly
2. **Local Access Only**: The API only accepts connections from localhost by default
3. **Certificate Management**: Import the self-signed certificate to avoid warnings
4. **Regular Key Rotation**: Change your API key periodically

### Vault Integrity

- Always test destructive operations (DELETE, PUT) in a test vault first
- Implement confirmation dialogs in your applications for deletions
- Consider keeping backups before bulk operations
- Respect Obsidian's file naming conventions

### Rate Limiting and Etiquette

While there are no hard rate limits, be mindful:
- Avoid rapid-fire requests that could impact Obsidian's performance
- Give adequate time for file system operations to complete
- Don't poll endpoints unnecessarily - use webhooks or events where possible

## Troubleshooting Common Issues

### "Certificate Not Trusted" Warnings
**Solution**: Download the certificate from `/obsidian-local-rest-api.crt` and add it to your system's trusted certificates.

### "404 File Not Found" for Known Files
**Common Causes**:
- Incorrect path format (check forward slashes)
- Missing file extension
- Case sensitivity issues on some systems

### PATCH Operations Not Working
**Checklist**:
- Verify target exists (heading text must match exactly)
- Check Target-Type spelling
- Ensure proper URL encoding for special characters
- Confirm block references exist in the target file

### Connection Refused Errors
**Verify**:
- Obsidian is running
- Plugin is enabled
- Correct port number (default: 27124)
- Firewall isn't blocking local connections

## Conclusion

The Obsidian Local REST API transforms your personal knowledge management system into a programmable platform. By understanding these endpoints and patterns, you can build powerful integrations that enhance your workflow while maintaining the security and integrity of your notes. Whether you're automating routine tasks, building custom interfaces, or integrating with other tools, this API provides the foundation for extending Obsidian far beyond its default capabilities.

Remember to start small, test thoroughly, and gradually build up to more complex integrations. The combination of Obsidian's powerful note-taking features with programmable access creates endless possibilities for managing and leveraging your knowledge.