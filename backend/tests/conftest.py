import pytest


@pytest.fixture
def sample_jenkinsfile():
    return """pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'mvn clean package'
            }
        }
        stage('Test') {
            steps {
                sh 'mvn test'
            }
        }
        stage('Deploy') {
            when { branch 'main' }
            steps {
                sh './deploy.sh'
            }
        }
    }
    post {
        always {
            junit '**/target/surefire-reports/*.xml'
        }
    }
}"""


@pytest.fixture
def sample_teamcity_kotlin():
    return """import jetbrains.buildServer.configs.kotlin.*
import jetbrains.buildServer.configs.kotlin.buildSteps.script

project {
    buildType(Build)
}

object Build : BuildType({
    name = "Build"
    steps {
        script {
            scriptContent = "echo Hello"
        }
    }
    triggers {
        vcs {}
    }
})"""


@pytest.fixture
def sample_teamcity_xml():
    return """<project>
    <build-type id="Build">
        <build-runners>
            <step type="simpleRunner">
                <param name="script.content" value="echo Hello"/>
            </step>
        </build-runners>
        <vcs-root id="MainVcs"/>
    </build-type>
</project>"""
