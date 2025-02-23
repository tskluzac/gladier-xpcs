from gladier import GladierBaseClient, generate_flow_definition


@generate_flow_definition(modifiers={
    'publish_gather_metadata': {'payload': '$.GatherXpcsMetadata.details.result[0]'}
})
class XPCSOnlineFlow(GladierBaseClient):
    globus_group = '368beb47-c9c5-11e9-b455-0efb3ba9a670'

    gladier_tools = [
        'gladier_xpcs.tools.TransferFromClutchToTheta',
        'gladier_xpcs.tools.PrePublish',
        'gladier_xpcs.tools.EigenCorr',
        # 'gladier_xpcs.tools.transfer_from_clutch_to_theta.TransferToClutch',
        'gladier_xpcs.tools.MakeCorrPlots',
        'gladier_xpcs.tools.gather_xpcs_metadata.GatherXPCSMetadata',
        'gladier_xpcs.tools.Publish',
    ]

