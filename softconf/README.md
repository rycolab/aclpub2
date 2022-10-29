## Configuration

Before running the script, a few preliminary steps must be taken. The repository contains a configuration file in JSON format called *config.json* where some variables must be set:

 * conf
 * track
 
These are the identifiers of the conference and the track, as they will be used in the ACL Anthology. FOr instance, for the System Demonstration track of ACL 2022, *conf* = *acl2022* and *track = demos*.

 * username
 * password
 
These are the credentials of a manager account for the conference or workshop on SOFTCONF.

Finally, two *webservices* must be activated in SOFTCONF before running the export script, and their link must be added to the configuration file.

In order to actovate Webservices, first of all check that *Enable webservices* in *Other tools* -> *Webservices* is set to *yes*.
Then, open the *Spreadsheet maker* and create two webservices, one for the *Submissions* spreadsheet, and one for the *Reviewer/Author Profile Information* spreadsheet, and select 'csv (UTF-8) before generating the webservice. Note their links (which can be found in the *Other tools* -> *Webservices* page, and put them respectively as values for the two last variables in the config file:

 * service_program_committee
 * service_papers
 
(put the full link, including https://...)

## Running

Once the config file is complete, you can run the export script with:

````python softconf2aclpub.py````

If Python modules are missing, they can be installed with pip using the provided requirement file:

````pip install -r requirements.txt````

If everything runs smoothly, the script will create a series of YAML files compatible with the format of aclpub2.

**Important:** the export and conversion from SOFTCONF is not fully automated. You will need to check and manually correct the YAML files produced by the script. This script needs to be thoroughly tested and adapted on a case by case basis.
