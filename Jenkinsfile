def getJobType() {
    def causes = "${currentBuild.rawBuild.getCauses()}"
    def job_type = "UNKNOWN"
    
    if(causes ==~ /.*TimerTrigger.*/)    { job_type = "cron" }
    if(causes ==~ /.*GitHubPushCause.*/) { job_type = "push" }
    if(causes ==~ /.*UserIdCause.*/)     { job_type = "manual" }
    if(causes ==~ /.*ReplayCause.*/)     { job_type = "manual" }
    
    return job_type
}

def notifyGitHub(status) {
    if(status == 'PENDING') { message = 'Building...' }
    if(status == 'SUCCESS') { message = 'Build succeeded!' }
    if(status == 'FAILURE') { message = 'Build failed!' }
    if(status == 'ERROR')   { message = 'Build aborted!' }
    step([$class: 'GitHubCommitStatusSetter', contextSource: [$class: 'ManuallyEnteredCommitContextSource', context: "JenkinsCI/${JOB_NAME}"], statusResultSource: [$class: 'ConditionalStatusResultSource', results: [[$class: 'AnyBuildResult', message: message, state: status]]]])
}

def isRelease() {
    return (GIT_BRANCH ==~ /.*\/release.*/) && (JOB_TYPE == "push")
}

def runCronJob() {
    sh "bash ${HOME}/workspace/build-scripts-cron/cronjob.sh $STAGE_NAME"
    if(isRelease())
      sh "rsync -n -avzh --stats ${INSTALLERS_DIR}/eman2.${STAGE_NAME}.unstable.sh ${DEPLOY_DEST}"
}

pipeline {
  agent {
    node { label 'jenkins-slave-1' }
  }
  
  triggers {
    cron('0 3 * * *')
  }
  
  environment {
    SKIP_UPLOAD = '1'
    JOB_TYPE = getJobType()
    INSTALLERS_DIR = '${HOME}/workspace/${STAGE_NAME}-installers'
    DEPLOY_DEST    = 'zope@ncmi.grid.bcm.edu:/home/zope/zope-server/extdata/reposit/ncmi/software/counter_222/software_136/'
    GIT_BRANCH_SHORT = sh(returnStdout: true, script: 'echo ${GIT_BRANCH##origin/}').trim()
    GIT_COMMIT_SHORT = sh(returnStdout: true, script: 'echo ${GIT_COMMIT:0:7}').trim()
  }
  
  stages {
    // Stages triggered by GitHub pushes
    stage('notify-pending') {
      when {
        expression { JOB_TYPE == "push" }
      }
      
      steps {
        notifyGitHub('PENDING')
      }
    }
    
    stage('build') {
      when {
        not { expression { JOB_TYPE == "cron" } }
        not { expression { isRelease() } }
      }
      
      parallel {
        stage('recipe') {
          steps {
            sh 'bash ci_support/build_recipe.sh'
          }
        }
        
        stage('no_recipe') {
          steps {
            sh 'source $(conda info --root)/bin/activate eman-env && bash ci_support/build_no_recipe.sh'
          }
        }
      }
    }
    
    // Stages triggered by cron or by a release branch
    stage('build-scripts-checkout') {
      when {
        anyOf {
          expression { JOB_TYPE == "cron" }
          expression { isRelease() }
        }
      }
      
      steps {
        sh 'cd ${HOME}/workspace/build-scripts-cron/ && git checkout jenkins && git pull --rebase'
      }
    }
    
    stage('centos6') {
      when {
        anyOf {
          expression { JOB_TYPE == "cron" }
          expression { isRelease() }
        }
        expression { SLAVE_OS == "linux" }
      }
      
      steps {
        runCronJob()
      }
    }
    
    stage('centos7') {
      when {
        anyOf {
          expression { JOB_TYPE == "cron" }
          expression { isRelease() }
        }
        expression { SLAVE_OS == "linux" }
      }
      
      steps {
        runCronJob()
      }
    }
    
    stage('mac') {
      when {
        anyOf {
          expression { JOB_TYPE == "cron" }
          expression { isRelease() }
        }
        expression { SLAVE_OS == "mac" }
      }
      
      steps {
        runCronJob()
      }
    }
    
    stage('build-scripts-reset') {
      when {
        anyOf {
          expression { JOB_TYPE == "cron" }
          expression { isRelease() }
        }
      }
      
      steps {
        sh 'cd ${HOME}/workspace/build-scripts-cron/ && git checkout master'
      }
    }
    
    stage('notify-push') {
      when {
        expression { JOB_TYPE == "push" }
      }
      
      steps {
        echo 'Setting GitHub status...'
      }
      
      post {
        success {
          notifyGitHub('SUCCESS')
        }
        
        failure {
          notifyGitHub('FAILURE')
        }
        
        aborted {
          notifyGitHub('ERROR')
        }
        
        always {
          emailext(recipientProviders: [[$class: 'DevelopersRecipientProvider']],  
                  subject: '[JenkinsCI/$PROJECT_NAME] ' + "($GIT_BRANCH_SHORT - ${GIT_COMMIT_SHORT})" + ' #$BUILD_NUMBER - $BUILD_STATUS!', 
                  body: '''${SCRIPT, template="groovy-text.template"}''')
        }
      }
    }
    
    stage('notify-cron') {
      when {
        expression { JOB_TYPE == "cron" }
      }
      
      steps {
        emailext(to: '$DEFAULT_RECIPIENTS',
                 subject: '[JenkinsCI/$PROJECT_NAME/cron] ' + "($GIT_BRANCH_SHORT - ${GIT_COMMIT_SHORT})" + ' #$BUILD_NUMBER - $BUILD_STATUS!', 
                 body: '''${SCRIPT, template="groovy-text.template"}''')
      }
    }
  }
}
