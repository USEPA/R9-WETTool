// abort existing build
def buildNumber = env.BUILD_NUMBER as int
if (buildNumber > 1) milestone(buildNumber - 1)
milestone(buildNumber)

node {
    try {
        dir('D:\\R9Web\\R9-WETTool') {
            checkout scm
            stage('update backend dependencies') {
                bat ".\\venv\\Scripts\\activate && pip install -r requirements.txt"
            }
            // need permissions to create test db
    //         stage('run backend test') {
    //             bat ".\\venv\\Scripts\\activate && python manage.py test --noinput"
    //         }
            stage('run migrations') {
                bat ".\\venv\\scripts\\activate && python manage.py migrate"
            }

    //     dir('.\\frontend') {
    //         stage('update frontend dependencies') {
    //             bat "npm i"
    //         }
    //         stage("build frontend") {
    //             bat "npm run build -- -c staging"
    //         }
    //     }
       }
        stage("Done") {
            slackSend(channel:"#r9-wet-tool-alerts", message: "WET Tool Staging Build COMPLETE")
//             input(message: "Approved for merge?")
            // todo: revert migrations on abort
        }


  } catch(Exception e) {
      slackSend(channel:"#r9-wet-tool-alerts", message: "WET Tool Staging Build FAILED or SUPERSEDED")
      slackSend(channel:"#r9-wet-tool-alerts", message: e)
    }
}
