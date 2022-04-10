# nested-github-runners-action

Reduce GitHub Actions costs by running multiple runners inside of a single GitHub Action Runner. 

`nested-github-runners-action` is a GitHub Action that spawns multiple self-hosted GitHub Action Runners inside a hosted GitHub Action Runner. Each self-hosted GitHub Runner runs in a container. The self-hosted runners are created at the repository-level for the repository that runs the Action. Each spawned runner is assigned a label based on the GitHub `run_id`, allowing other jobs in the Workflow to be configured to use the spawned runners.

## Example Usage

```
jobs:
  create-nested-runners:
    runs-on: ubuntu-latest
    steps:
      - name: Run Multiple GitHub Runners in Runner
        uses: dougcalobrisi/nested-github-runners-action@v0.9
        with:
          github-token: ${{ secrets.GH_TOKEN }}
          runners: 3
  job1:
    runs-on: nested-${{ github.run_id }}
    steps:
      - name: echo hostname
        run: echo `hostname`
  job2:
    runs-on: nested-${{ github.run_id }}
    steps:
      - name: echo hostname
        run: echo `hostname`
  job3:
    runs-on: nested-${{ github.run_id }}
    steps:
      - name: echo hostname
        run: echo `hostname`
```

## Cost Reduction
### Examples

#### Building git 
In this test, we build `git` in multiple parallel jobs, with either 3 or 4 concurrent builds. We can see while the cost savings comes at the expense of overall time, we can save up to 50% while only slightly increasing overall time, by adding additional hosted runners with `nested-github-runners-action`. 
| Nested?    | Parallel Jobs | Hosted Runners | Total Time     | Billable Time   | Cost          | Savings   |
| :--------: | :-----------: | :------------: | :------------: | :-------------: | :-----------: | :-------: |
| no         | 3             | 3              | 3m 17s         | 12m             | $0.096        | na        |
| *yes*      | 3             | 1              | 5m 48s         | 6m              | $0.048        | 50%       |


| Nested?    | Parallel Jobs | Hosted Runners | Total Time     | Billable Time   | Cost          | Savings   |
| :--------: | :-----------: | :------------: | :------------: | :-------------: | :-----------: | :-------: |
| no         | 4             | 4              | 3m 17s         | 16m             | $0.128        | na        |
| *yes*      | 4             | 1              | 7m 12s         | 8m              | $0.064        | 50%       |
| *yes*      | 4             | 2              | 4m 21s         | 10m             | $0.08         | 37.5%     |

#### Django Tests on Multiple Python Versions
In this test, we run Django's test suite on multiple Python versions - Python 3.8, 3.9, and 3.10. Billing time is reduced by approximately 23% by using `nested-github-runners-action`, with the tradeoff of the entire Workflow taking a little more than twice as long. 
| Nested?    | Parallel Jobs | Hosted Runners | Total Time     | Billable Time   | Cost          | Savings   |
| :--------: | :-----------: | :------------: | :------------: | :-------------: | :-----------: | :-------: |
| no         | 3             | 3              | 8m 28s         | 26m             | $0.208        | na        |
| *yes*      | 3             | 1              | 19m 9s         | 20m             | $0.16         | 23%       |

#### Express Tests for 16 Versions of Node
In this test, we run the ExpressJS test suite against 16 different versions of Node. Again, we see significant cost reduction of up to 44% by using `nested-github-runners-action` to spawn multiple ephemeral self-hosted runners. 

| Nested?    | Parallel Jobs | Hosted Runners | Total Time     | Billable Time   | Cost          | Savings   |
| :--------: | :-----------: | :------------: | :------------: | :-------------: | :-----------: | :-------: |
| no         | 16            | 16             | 59s            | 16m             | $0.128        | na        |
| *yes*      | 16            | 1              | 8m 42s         | 9m              | $0.072        | 44%       |
| *yes*      | 16            | 2              | 4m 36s         | 9m              | $0.072        | 44%       |
| *yes*      | 16            | 4              | 2m 28s         | 10m             | $0.08         | 37.5%     |

## Using `runs-on`
You *must* specify `runs-on: nested-${{ github.run_id }}` for any jobs in the Workflow that should use the spawned runners. This is how GitHub Actions knows to only assign the job to the self-hosted runners created by `nested-github-runners-action`.

## GitHub Token
You must specify a GitHub Personal Access Token using the `github-token` input. This token must have write access to this repository. You can find more information on creating such a token in the [GitHub Documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token).

## Runner Docker Image
By default, `nested-github-runners-action` leverages the `dougcalobrisi/nested-github-runner` Docker image, which is built from the [`docker/`](docker) directory. 

A custom image could be specified using the `runner-image` input. This custom image would need to be based on `dougcalobrisi/nested-github-runner` as specified in the [`docker/`](docker) directory. 

## Shared Volume
By default, a shared volume (`/shared`) is created and shared amongst the spawned runners, allowing the jobs of the workflow to easily share data. The shared volume functionality can be disabled by setting the `shared-volume` input to `false`. Additionally, the `shared-volume-host-path` input can be used to provide a specific path on the host runner for the shared volume.

## Runner Prefix and Labels
By default, each runner uses `nested` as both the prefix of each runner's name, and as an assigned label. The prefix that each runner uses can be changed from the defaults using the `runner-prefix` input. An additional runner label can also be assigned using the `runner-label` input.

:bangbang: | If `runner-prefix` is specified, you must also use the same prefix in `runs-on` for each Workflow job.
:---: | :---


## Multiple Hosted Runners in a Single Workflow
By using multiple hosted runners, you can reduce cost without a great increase to total workflow completion time.
To use multiple hosted runners, you can use the GitHub Actions `matrix` strategy to launch multiple Jobs running `nested-github-runners-action`. Each instance (Job) will create the configured number of self-hosted GitHub Actions Runners in its VM. Since the `matrix` strategy expects unique names (or variable values) for each Job it should create, specify the range of required `nested-github-runners-action` jobs. For example, for three, you could specify `[1,2,3]` or `[one,two,three]`.

The following example would create 12 Job runners in total - three `nested-github-runners-action` jobs, each with 4 runners.
```
jobs:
  create-nested-runners:
    strategy:
      matrix:
        runners: [1,2,3]
    runs-on: ubuntu-latest
    steps:
      - name: Run Multiple GitHub Runners in Runner
        uses: dougcalobrisi/nested-github-runners-action@v0.9
        with:
          github-token: ${{ secrets.GH_TOKEN }}
          runners: 4
```

## Limitations
- GitHub Self-Hosted Runners running in Docker do not currently support running containers via `container:` in a Job. Therefore, `nested-github-runners-action` does not currently support it, either.

## Inputs

| Input             | Required ?    | Default       | Usage                                                                   |
| ----------------- | ------------- | ------------- | ----------------------------------------------------------------------- |
| `github-token`    | yes           |               | GitHub Personal Access Token (PAT) with write permissions for the repo  |
| `runners`         | yes           | 1             | number of runners to create |
| `runner-image`    | no            | `dougcalobrisi/nested-github-runner:latest` | Docker GitHub Actions Runner Image |
| `runner-prefix`   | no            | `nested`  | prefix to use for each runner's name |                                   
| `runner-label`    | no            | `nested`  | label to add to each runner |
| `shared-volume`   | no            | `/shared`     | path for shared volume in each runner, or `false` to disable shared volume |
| `shared-volume-host-path` | no    | `/shared`     | path for shared volume on host runner |
| `docker-in-docker`| no            | `true`        | disable Docker-in-Docker functionality |

## Usage
```
name: Runners in Runner with nested-github-runners-action

on:
  workflow_dispatch:

jobs:
  create-runners:
    runs-on: ubuntu-latest
    steps:
    - name: Run Multiple GitHub Runners in Runner
      uses: dougcalobrisi/nested-github-runners-action@v0.9
      with:
        runners: 3
        github-token: ${{ secrets.GH_TOKEN }}

  runner1:
    runs-on: nested-${{ github.run_id }}
    steps:
    - name: echo hostname
      run: |
        echo `hostname`

  runner2:
    runs-on: nested-${{ github.run_id }}
    steps:
    - name: echo hostname
      run: |
        echo `hostname`

  runner3:
    runs-on: nested-${{ github.run_id }}
    steps:
    - name: echo hostname
      run: |
        echo `hostname`
```

### Example of Using All Inputs
```
- name: Run Multiple GitHub Runners in Runner
  uses: dougcalobrisi/nested-github-runners-action@v0.9
  with:
    runners: 3
    github-token: ${{ secrets.GH_TOKEN }}
    runner-image: dougcalobrisi/nested-github-runner:latest
    runner-prefix: nested
    runner-label: nested
    shared-volume: /shared
    shared-volume-host-path: /shared
    docker-in-docker: true
```