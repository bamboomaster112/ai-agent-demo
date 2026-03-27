"""Tests for the detection engine."""

from app.detection.patterns import detect_platform_and_format, detect_config_type


def test_detect_jenkins_groovy(sample_jenkinsfile):
    result = detect_platform_and_format(sample_jenkinsfile)
    assert result["source_platform"] == "jenkins"
    assert result["source_format"] == "groovy"
    assert result["confidence"] >= 0.5


def test_detect_jenkins_with_filename(sample_jenkinsfile):
    result = detect_platform_and_format(sample_jenkinsfile, filename="Jenkinsfile")
    assert result["source_platform"] == "jenkins"
    assert result["confidence"] >= 0.7


def test_detect_teamcity_kotlin(sample_teamcity_kotlin):
    result = detect_platform_and_format(sample_teamcity_kotlin)
    assert result["source_platform"] == "teamcity"
    assert result["source_format"] == "kotlin_dsl"
    assert result["confidence"] >= 0.5


def test_detect_teamcity_xml(sample_teamcity_xml):
    result = detect_platform_and_format(sample_teamcity_xml)
    assert result["source_platform"] == "teamcity"
    assert result["source_format"] == "xml"
    assert result["confidence"] >= 0.5


def test_detect_config_type_complete_pipeline(sample_jenkinsfile):
    result = detect_config_type(sample_jenkinsfile)
    assert result["config_type"] == "complete_pipeline"


def test_detect_config_type_shared_library():
    lib_code = """@Library('my-shared-lib') _

def call(Map config) {
    pipeline {
        agent any
        stages {
            stage('Build') {
                steps { sh 'make build' }
            }
        }
    }
}"""
    result = detect_config_type(lib_code)
    assert result["config_type"] == "shared_library"


def test_detect_teamcity_kotlin_with_kts_filename():
    code = "project { buildType { name = 'Build' } }"
    result = detect_platform_and_format(code, filename="settings.kts")
    assert result["source_platform"] == "teamcity"
    assert result["source_format"] == "kotlin_dsl"
