# CLUF

CLUster-based Framework (CLUF) if a software clustering for bug-proneness analysis.

Please see the paper for details: 


## Project structure
An breif introduction of each folder and their content in this repository.
+ `CLUF`: source code of CLUF
+ `input`: input file and configuration
+ `git_tag`: souce code of project release
+ `git_main`: source code of higher project release
+ `data_middle`: derived data of analyzed project 
+ `data_cluster`: cluster parition
+ `data_result`: analyzed result

## Requirements

On Windows:
* Python 3.7
* Code2Vec
    + Download Token Vectors of Code2Vec through [Link](https://s3.amazonaws.com/code2vec/model/token_vecs.tar.gz)
    + Unzip downloaded package 
* Scitools Understand
    + Make sure Understand Python library is setup correctly through [Setup Tutorials](https://support.scitools.com/support/solutions/articles/70000582852-getting-started-with-the-python-api).

## Configuration

### Step 0: Cloning this repository

    git clone https://github.com/CLUF-tool/CLUF.git
    cd CLUF

### Step 2: Configuring root path

* Find and open `<Your local repository path>\CLUF\CLUF\utils\GlobalVar.py`

* Setup `<root_path>` in GlobalVar.py as `<Your local repository path>`

### Step 3: Conguring Code2Vec

* Put unzipped Token Vectors into `<Your local repository path>\CLUF\input\c2v_token_vecs`

## Usage

### Step 1: Configuring analyzed project

* Find and open `<Your local repository path>\CLUF\input\input_project.csv`
* Edit arguments of :
    + `project`: analyzed project name, eg: atlas
    + `exp_version`: analyzed project release, eg: atlas-1.2.0
    + `exp_branch`: git branch of project release, eg: release-1.2.0-rc3
    + `new_version`: higher release of analyzed project release, eg: 2.3.0
    + `new_branch`: git branch of higher release, eg: release-2.3.0
    + `jira_key`: filename of Jira data, eg: atlas

### Step 2: Exporting Jira data
* Export the bug data as CSV format from jira 
* Put it in the `<Your local repository path>\CLUF\input\jira` directory

### Step 3: Analyzing project via understand
* Create understand project of `exp_version`

### Step 4: Running CLUF
* Run `_1_get_data.py`
    + **description:** According to the configured project and bug data, first clone the repository, then export the commit log and bug-fix log, and finally save the data in historical_data.csv
* Run `_2_get_matrix.py`
    + **description:** Generate coMatrix and seMatrix, and export loc of each file in project
* Run `_3_get_clusters.py`
    + **description:** Generate clusters according coMatrix and seMatrix
* Run `_4_get_high_risk_clusters.py`
    + **description:** Identify high-risk clusters according bug data, this step also output result of RQ1.
* Run `performance.py`
    + **description:** Output result of RQ2.
* Compare data with other cluster algorithm
    +  **description:** If you get other cluster result of RQ1 and RQ2 and want to , you can first tidy compared data through Cliff effect size,first you need to `tidy_data.py`, then compare them though `cliff.py`

## Example
We have placed an Example project, atlas, in this repository. It has generated all the derived data of atlas include coMatrix and seMatrix. If you don't configure Understand API correctly, you can start from `Run _3_get_clusters.py`.