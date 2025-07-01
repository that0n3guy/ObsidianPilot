```
-  async def search_notes(
       387 -      query: str,
       388 -      context_length: int = 100,
       389 -      ctx=None
       390 -  ) -> dict:
       391 -      """
       392 -      Search for notes containing specific text or matching search criteria.
       393 -      
       394 -      Use this tool to find notes by content, title, metadata, or properties. Supports
       395 -      multiple search modes with special prefixes:
       396 -      
       397 -      Search Syntax:
       398 -      - Content search (default): Just type your query to search within note content
       399 -        Example: "machine learning" finds notes containing this text
       400 -      - Path/Title search: Use "path:" prefix to search by filename or folder
       401 -        Example: "path:Daily/" finds all notes in Daily folder
       402 -        Example: "path:Note with Images" finds notes with this in their filename
       403 -      - Tag search: Use "tag:" prefix to search by tags
       404 -        Example: "tag:project" or "tag:#project" finds notes with the project tag
       405 -      - Property search: Use "property:" prefix to search by frontmatter properties
       406 -        Example: "property:status:active" finds notes where status = active
       407 -        Example: "property:priority:>2" finds notes where priority > 2
       408 -        Example: "property:assignee:*john*" finds notes where assignee contains "john"
       409 -        Example: "property:deadline:*" finds notes that have a deadline property
       410 -      - Combined searches are supported but limited to one mode at a time
       411 -      
       412 -      Property Operators:
       413 -      - ":" or "=" for exact match (property:name:value)
       414 -      - ">" for greater than (property:priority:>3)
       415 -      - "<" for less than (property:age:<30)
       416 -      - ">=" for greater or equal (property:score:>=80)
       417 -      - "<=" for less or equal (property:rating:<=5)
       418 -      - "!=" for not equal (property:status:!=completed)
       419 -      - "*value*" for contains (property:title:*project*)
       420 -      - "*" for exists (property:tags:*)
       421 -      
       422 -      Args:
       423 -          query: Search query with optional prefix (path:, tag:, property:, or plain text)
       424 -          context_length: Number of characters to show around matches (default: 100)
       425 -          ctx: MCP context for progress reporting
       426 -          
       427 -      Returns:
       428 -          Dictionary containing search results with matched notes and context
       429 -          
       430 -      Examples:
       431 -          >>> # Search by content
       432 -          >>> await search_notes("machine learning algorithms", ctx=ctx)
       433 -          
       434 -          >>> # Search by filename/path
       435 -          >>> await search_notes("path:Project Notes", ctx=ctx)
       436 -          
       437 -          >>> # Search by tag
       438 -          >>> await search_notes("tag:important", ctx=ctx)
       439 -          
       440 -          >>> # Search by property
       441 -          >>> await search_notes("property:status:active", ctx=ctx)
       442 -          >>> await search_notes("property:priority:>2", ctx=ctx)
       443 -      """
       444 -      # Validate parameters
       445 -      is_valid, error = validate_search_query(query)
       446 -      if not is_valid:
       447 -          raise ValueError(error)
       448 -      
       449 -      is_valid, error = validate_context_length(context_length)
       450 -      if not is_valid:
       451 -          raise ValueError(error)
       452 -      
       453 -      if ctx:
       454 -          ctx.info(f"Searching notes with query: {query}")
       455 -      
       456 -      vault = get_vault()
       457 -      
       458 -      try:
       459 -          # Get vault size once for performance checks
       460 -          all_notes = await vault.list_notes(recursive=True)
       461 -          vault_size = len(all_notes)
       462 -          
       463 -          # Handle special search syntax
       464 -          if query.startswith("tag:"):
       465 -              # Tag search
       466 -              tag = query[4:].lstrip("#")
       467 -              results = await _search_by_tag(vault, tag, context_length)
       468 -          elif query.startswith("path:"):
       469 -              # Path search
       470 -              path_pattern = query[5:]
       471 -              results = await _search_by_path(vault, path_pattern, context_length)
       472 -          elif query.startswith("property:"):
       473 -              # Property search
       474 -              results = await _search_by_property(vault, query, context_length)
       475 -          else:
       476 -              # Regular content search - use fast search for large vaults
       477 -              try:
       478 -                  if vault_size > 500:
       479 -                      # Use fast search for large vaults
       480 -                      from ..tools.fast_search import fast_search_notes
       481 -                      fast_result = await fast_search_notes(query, max_results=200, context_length=context_length)
       482 -                      
       483 -                      # Convert fast search results to legacy format
       484 -                      results = []
       485 -                      for item in fast_result['results']:
       486 -                          results.append({
       487 -                              "path": item["path"],
       488 -                              "score": item["score"],
       489 -                              "matches": [query],
       490 -                              "context": item["context"]
       491 -                          })
       492 -                  else:
       493 -                      # Use legacy search for small vaults
       494 -                      results = await vault.search_notes(query, context_length)
       495 -              except Exception:
       496 -                  # Fall back to fast search if regular search fails
       497 -                  from ..tools.fast_search import fast_search_notes
       498 -                  try:
       499 -                      fast_result = await fast_search_notes(query, max_results=200, context_length=context_length)
       500 -                      results = []
       501 -                      for item in fast_result['results']:
       502 -                          results.append({
       503 -                              "path": item["path"],
       504 -                              "score": item["score"],
       505 -                              "matches": [query],
       506 -                              "context": item["context"]
       507 -                          })
       508 -                  except Exception:
       509 -                      # Last resort - return empty results with helpful message
       510 -                      results = []
       511 -          
       512 -          # Check if we used fast search and add helpful message
       513 -          used_fast_search = not query.startswith(("tag:", "path:", "property:")) and vault_size > 500
       514 -          
       515 -          # Return standardized search results structure
       516 -          result = {
       517 -              "results": results,
       518 -              "count": len(results),
       519 -              "query": {
       520 -                  "text": query,
       521 -                  "context_length": context_length,
       522 -                  "type": "tag" if query.startswith("tag:") else "path" if query.startswith("path:") else "property" if 
     query.startswit
           - h("property:") else "content"
       523 -              },
       524 -              "truncated": False  # We don't have a hard limit on results currently
       525 -          }
       526 -          
       527 -          if used_fast_search:
       528 -              result["performance_note"] = "Used fast search (FTS5) due to large vault size. For more advanced search options, try 
     'fas
           - t_search_notes_tool' directly."
       529 -          
       530 -          return result
       531 -      except Exception as e:
       532 -          if ctx:
       533 -              ctx.info(f"Search failed: {str(e)}")
       534 -          # Return standardized error structure
       535 -          return {
       536 -              "results": [],
       537 -              "count": 0,
       538 -              "query": {
       539 -                  "text": query,
       540 -                  "context_length": context_length,
       541 -                  "type": "tag" if query.startswith("tag:") else "path" if query.startswith("path:") else "property" if 
     query.startswit
           - h("property:") else "content"
       542 -              },
       543 -              "truncated": False,
       544 -              "error": f"Search failed: {str(e)}"
       545 -          }
       546 -  
       547 -  

```