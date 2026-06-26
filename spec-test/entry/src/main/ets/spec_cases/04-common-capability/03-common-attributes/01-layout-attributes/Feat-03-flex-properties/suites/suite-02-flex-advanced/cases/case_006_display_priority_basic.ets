
@Entry
@Component
export struct Case006DisplayPriorityBasic {
  build() {
    Flex({ direction: FlexDirection.Row }) {
      // High priority - should be visible
      Text('High')
        .id('N_F03_S02_C006_TARGET_HIGH')
        .width(120)
        .height(50)
        .backgroundColor('#4CAF50')
        .displayPriority(2)
      // Low priority - should be hidden when space insufficient
      Text('Low')
        .id('N_F03_S02_C006_TARGET_LOW')
        .width(120)
        .height(50)
        .backgroundColor('#F44336')
        .displayPriority(1)
    }
    .id('N_F03_S02_C006_PARENT')
    .width(200)
    .height(100)
  }
}
