
@Entry
@Component
export struct Case003PaddingBasic {
  build() {
    Column() {
      // Container with padding, child should have content area reduced
      Column() {
        Text('Inner')
          .id('N_F01_S02_C003_TARGET')
          .width('100%')
          .height('100%')
          .backgroundColor('#FF9800')
      }
      .id('N_F01_S02_C003_PARENT')
      .width(100)
      .height(80)
      .padding(10)
      .backgroundColor('#E0E0E0')
    }
    .width(300)
    .height(200)
  }
}
