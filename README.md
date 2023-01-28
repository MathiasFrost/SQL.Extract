# SQL.Extract - _Python_

Extract SQL queries from applications and turn them into `.sql` files in the following structure:

- Class directory
    - Method directory
        - SQL file

## Example

The class:

```c#
[ApiController, Route("[controller]/[action]")]
public class UserController : ControllerBase
{
    [HttpGet]
    public IActionResult Ping()
    {
        return Ok();
    }

    [HttpGet("{id:long}/{name:required}")]
    public async Task<string> Get(long id, string name)
    {
        return MyDb.Users.FromSqlInterpolated($@"
SELECT * FROM dbo.[User]
WHERE Id = {id} AND Name = {name.Trim()}
        ");
    }

    [HttpDelete("{id:long}")]
    public void Delete(long id) => 
        MyDb.Users.FromSqlInterpolated($@"
DELETE FROM dbo.[User]
WHERE id = {id}
    ");
}
```

The command:

```shell
python main.py MyAPI SomeDB.SQL
```

The result:

- SomeDB.SQL
    - MyAPI
        - User
            - Get.sql
            - Delete.sql

With sql files:  
Get.sql:

```sql
SELECT *
FROM dbo.[User]
WHERE Id = :id AND Name = : name
```

Delete.sql

```sql
DELETE
FROM dbo.[User]
WHERE id = :id

```