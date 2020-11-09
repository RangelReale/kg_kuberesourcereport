from kubragen import KubraGen
from kubragen.consts import PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE
from kubragen.object import Object
from kubragen.option import OptionRoot
from kubragen.options import Options
from kubragen.output import OutputProject, OD_FileTemplate, OutputFile_ShellScript, OutputFile_Kubernetes, \
    OutputDriver_Print
from kubragen.provider import Provider

from kg_kuberesourcereport import KubeResourceReportBuilder, KubeResourceReportOptions, \
    KubeResourceReportOptions_Default_Resources_Deployment, KubeResourceReportOptions_Default_Resources_DeploymentNGINX

kg = KubraGen(provider=Provider(PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE), options=Options({
    'namespaces': {
        'mon': 'app-monitoring',
    },
}))

out = OutputProject(kg)

shell_script = OutputFile_ShellScript('create_gke.sh')
out.append(shell_script)

shell_script.append('set -e')

#
# OUTPUTFILE: app-namespace.yaml
#
file = OutputFile_Kubernetes('app-namespace.yaml')

file.append([
    Object({
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {
            'name': 'app-monitoring',
        },
    }, name='ns-monitoring', source='app', instance='app')
])

out.append(file)
shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

shell_script.append(f'kubectl config set-context --current --namespace=app-monitoring')

#
# SETUP: kube-resource-report
#
ksm_config = KubeResourceReportBuilder(kubragen=kg, options=KubeResourceReportOptions({
    'namespace': OptionRoot('namespaces.mon'),
    'basename': 'myksm',
    'config': {
    },
    'kubernetes': {
        'resources': {
            'deployment': KubeResourceReportOptions_Default_Resources_Deployment(),
            'deployment-nginx': KubeResourceReportOptions_Default_Resources_DeploymentNGINX(),
        },
    }
}))

ksm_config.ensure_build_names(ksm_config.BUILD_ACCESSCONTROL, ksm_config.BUILD_SERVICE)

#
# OUTPUTFILE: KubeResourceReport-config.yaml
#
file = OutputFile_Kubernetes('kuberesourcereport-config.yaml')
out.append(file)

file.append(ksm_config.build(ksm_config.BUILD_ACCESSCONTROL))

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# OUTPUTFILE: KubeResourceReport.yaml
#
file = OutputFile_Kubernetes('KubeResourceReport.yaml')
out.append(file)

file.append(ksm_config.build(ksm_config.BUILD_SERVICE))

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# Write files
#
out.output(OutputDriver_Print())
# out.output(OutputDriver_Directory('/tmp/build-gke'))
