# TODO for the ELiDa database project:

* Populate the ELIDA data models with the data from TianTian's masters project output (probably less than half of the 
  ExoMol molecules though?)
* In preparation for easy syncing between ExoMol database and ELiDa database:
  * Code a mapping between ExoMol formulas and the most abundant isotopologues
  * Code a script requesting ExoMol database contents, figuring out which exactly molecules, isotopologues, recommended 
    datasets, states, and transitions should make it's way into the ExoMol database, and outputting some sort of 
    *diff* between the ExoMol data available and the content of the ELiDa database.
* Implement the API (public, read-only, responses will be strictly only json files)
  * Test the API
* Implement the web interface
* Host the database
* Publish the database
* Code some automatic ExoMol -> ELiDa syncing utility
  * Built around the script described in the second point, and around TianTian's code implementing the actual lifetimes
    calculation from the ExoMol data.