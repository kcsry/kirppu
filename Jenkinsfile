def image = "tracon/kirppu:build-${env.BUILD_NUMBER}"

stage("Build") {
  node {
    checkout scm
    sh "docker build --tag ${image} ."
  }
}

// stage("Test") {
//   node {
//     sh """
//       docker run \
//         --rm \
//         --link jenkins.tracon.fi-postgres:postgres \
//         --env-file ~/.kirppu.env \
//         ${image} \
//         pip install -r requirements-dev.txt && py.test --cov . --doctest-modules
//     """
//   }
// }

stage("Push") {
  node {
    sh "docker tag ${image} tracon/kirppu:latest && docker push tracon/kirppu:latest && docker rmi ${image}"
  }
}

stage("Deploy") {
  node {
    git url: "git@github.com:tracon/ansible-tracon"
    sh """
      ansible-playbook \
        --vault-password-file=~/.vault_pass.txt \
        --user root \
        --limit nuoli.tracon.fi \
        --tags kirppu-deploy \
        tracon.yml
    """
  }
}
