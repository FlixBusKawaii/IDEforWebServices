# IDEforWebServices
Two students trying to make a "Web Service" where you can code like you are on Google Docs

## How to run the code 
To run the code from the root 
```bash 
docker-compose up
```

full command to clear the cache and build the docker
```bash 
docker-compose down -v && docker-compose build --no-cache && docker-compose up
```

>[!WARNING]
> If the C compiler doesen't work you need to change the CMODE of the ide_projects file with this command
>
```bash 
chmod 777 ide_projects
```
