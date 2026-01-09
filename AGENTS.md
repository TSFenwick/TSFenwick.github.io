# AGENTS instructions

## The Project

This project is to create a simple fast-loading website to direct people to local businesses. In a limited geographical area.
People will most often access the website via a qr code that is tied to a certain location.
The businesses should be filterable by different things like distance, category, is open now, or will open soon.
The website should be fast to load and have a good user experience. This project uses uv commands.

## Building the website

```shell
uv run build.py
```

This command requires `data.toml` to exist. It's where all the information used to actually generate the website should exist. 

## Building the QR codes

```shell
uv run generate_qr.py
```

this command requires `data.toml` to exist. It uses information in it to generate qr codes for each location.

## Data format 

See `data.toml` for the format of the data for a business and for a location.