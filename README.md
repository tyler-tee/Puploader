# Puploader
<div align="center">
  
[![Pylint](https://github.com/tyler-tee/Puploader/actions/workflows/pylint.yml/badge.svg?branch=master&event=push)](https://github.com/tyler-tee/Puploader/actions/workflows/pylint.yml)

</div>
<table>
<tr>
<td>
Simple Flask app built to receive, store, and serve dog photos. Uploading non-dog photos works fine, but why would you want to?
</td>
</tr>
</table>

![Puploader](https://user-images.githubusercontent.com/64701075/156957751-10d46cb2-9b73-4432-8097-417181d9e62e.png)

## Preview
- Current iteration live [here](https://puploader.herokuapp.com)

## Current Features
- Multi-file upload
- Live gallery
- Local shelters/adoptable dogs information
- User management supported by a MongoDB backend

## Built with 

- [Flask](https://flask.palletsprojects.com/en/2.0.x/) - "Web development, one drop at a time."
- [MongoDB](https://www.mongodb.com/) - "Build faster, build smarter."

## Development
Contribution welcome.

To fix a bug or enhance an existing module, follow these steps:

- Fork the repo
- Create a new branch (`git checkout -b improve-feature`)
- Make the appropriate changes in the files
- Add changes to reflect the changes made
- Commit your changes (`git commit -am 'Improve feature'`)
- Push to the branch (`git push origin improve-feature`)
- Create a Pull Request

## To-Do
- [ ] Add local Veterinary clinic information
- [ ] Add Okta integration for authentication
- [X] Add animal-friendly charities to 'Resources' (25%)
- [X] Add S3 integration for Heroku deployment
- [X] Add Google login for authentication
- [X] Add location input/collection for resources (Shelters/Adoptable pets)

## License
[MIT](https://choosealicense.com/licenses/mit/)
